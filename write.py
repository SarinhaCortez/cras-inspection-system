conf = """
inference_address=http://127.0.0.1:8083
management_address=http://127.0.0.1:8081
metrics_address=http://127.0.0.1:8082
enable_token_auth=false

"""

with open('config.properties', 'w') as f:
    f.write(conf)
    
#using Detr tuned by Barbara, write the actual model

model_py = """
import torch
import pytorch_lightning as pl
from transformers import DetrForObjectDetection, DetrImageProcessor


class Detr(pl.LightningModule):

    def __init__(self, lr, lr_backbone, weight_decay):
        super().__init__()
        self.model = DetrForObjectDetection.from_pretrained(
            pretrained_model_name_or_path="facebook/detr-resnet-50",
            num_labels=5,
            ignore_mismatched_sizes=True
        )

        self.lr = lr
        self.lr_backbone = lr_backbone
        self.weight_decay = weight_decay

    def forward(self, pixel_values, pixel_mask):
        return self.model(pixel_values=pixel_values, pixel_mask=pixel_mask)

    def common_step(self, batch, batch_idx):
        pixel_values = batch["pixel_values"]
        pixel_mask = batch["pixel_mask"]
        labels = [{k: v.to(self.device) for k, v in t.items()} for t in batch["labels"]]

        outputs = self.model(pixel_values=pixel_values, pixel_mask=pixel_mask, labels=labels)

        loss = outputs.loss
        loss_dict = outputs.loss_dict

        return loss, loss_dict

    def training_step(self, batch, batch_idx):
        loss, loss_dict = self.common_step(batch, batch_idx)
        self.log("training_loss", loss)
        for k,v in loss_dict.items():
            self.log("train_" + k, v.item())

        return loss

    def validation_step(self, batch, batch_idx):
        loss, loss_dict = self.common_step(batch, batch_idx)
        self.log("validation/loss", loss)
        for k, v in loss_dict.items():
            self.log("validation_" + k, v.item())

        return loss

    def configure_optimizers(self):
        # DETR authors decided to use different learning rate for backbone
        param_dicts = [
            {
                "params": [p for n, p in self.named_parameters() if "backbone" not in n and p.requires_grad]},
            {
                "params": [p for n, p in self.named_parameters() if "backbone" in n and p.requires_grad],
                "lr": self.lr_backbone,
            },
        ]
        return torch.optim.AdamW(param_dicts, lr=self.lr, weight_decay=self.weight_decay)

"""
with open('detr_model/model.py', 'w') as f:
    f.write(model_py)


handler_py = """

from ts.torch_handler.base_handler import BaseHandler
import torch
from torchvision import transforms
from PIL import Image
import io
import os
from model import Detr #using Detr tuned by Barbara, write the actual model
import numpy as np
#from torchvision.ops import box_cxcywh_to_xyxy  VOLTAR A POR PARA O SERVIDOR
import json
import zlib
import safetensors.torch
from transformers import DetrImageProcessor

#pytorch's colab version does not have box_cxcywh_to_xyxy

def box_cxcywh_to_xyxy(boxes):

    x_c, y_c, w, h = boxes.unbind(-1)
    b = [(x_c - 0.5 * w), (y_c - 0.5 * h),
         (x_c + 0.5 * w), (y_c + 0.5 * h)]

    return torch.stack(b, dim=-1)
##################################

class DetrHandler(BaseHandler):
    def initialize(self, context):
        model_dir = context.system_properties["model_dir"]

        # Initialize the model
        self.model = Detr(lr=1e-4, lr_backbone=1e-5, weight_decay=1e-4)
        state_dict_path = os.path.join(model_dir, "model.safetensors")
        self.model.load_state_dict(safetensors.torch.load_file(state_dict_path))

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device).eval()

        # Initialize the processor 
        self.processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")

        # Define parameters for postprocessing
        self.confidence_threshold = 0.0
        self.max_predictions = 100

    def preprocess(self, data):
      processed_images = []
      pixel_masks = []

      for datadict in data:
          for dictkey, image_data in datadict.items():
            
              if isinstance(image_data, bytearray):
                  image_data = bytes(image_data)
                  image = Image.open(io.BytesIO(image_data)).convert('RGB')

                  inputs = self.processor(images=image, return_tensors="pt")
                  processed_images.append(inputs["pixel_values"].squeeze(0))
                  pixel_masks.append(inputs["pixel_mask"].squeeze(0))
              else:
                  raise ValueError("Expected image data as bytearray")

      batch_tensor = torch.stack(processed_images)
      pixel_masks_tensor = torch.stack(pixel_masks)

      return batch_tensor, pixel_masks_tensor

    def inference(self, image_tensor, pixel_mask_tensor):
        try:
            image_tensor = image_tensor.to(self.device)
            pixel_mask_tensor = pixel_mask_tensor.to(self.device)


            with torch.no_grad():
                output = self.model(pixel_values=image_tensor, pixel_mask=pixel_mask_tensor)

                required_keys = {'logits', 'pred_boxes'}
                if not required_keys.issubset(output.keys()):
                    raise KeyError(f"Model output missing required keys: {required_keys - output.keys()}")

                

                # convert to CPU and numpy format for postprocessing
                output_np = {}
                for k, v in output.items():
                    if isinstance(v, torch.Tensor):
                        output_np[k] = v.cpu().numpy()
                    else:
                        raise TypeError(f"Unexpected type for output key '{k}': {type(v)}")

                return output_np

        except Exception as e:
            raise RuntimeError("Error during inference") from e

    def postprocess(self, output):
        try:
            logits = torch.tensor(output['logits'])
            pred_boxes = torch.tensor(output['pred_boxes'])

            batch_size = logits.shape[0]
            results = {"boxes": [], "labels": [], "scores": []}

            for i in range(batch_size):
                probabilities = torch.softmax(logits[i], dim=-1)
                scores, labels = probabilities[..., :-1].max(dim=-1)
                keep = scores > self.confidence_threshold

                scores = scores[keep]
                labels = labels[keep]
                boxes = pred_boxes[i][keep]

                if len(scores) > self.max_predictions:
                    topk = scores.topk(self.max_predictions, sorted=False)
                    scores = topk.values
                    labels = labels[topk.indices]
                    boxes = boxes[topk.indices]

                boxes = box_cxcywh_to_xyxy(boxes)

                results["boxes"].append(boxes.cpu().numpy().tolist())
                results["labels"].append(labels.cpu().numpy().tolist())
                results["scores"].append(scores.cpu().numpy().tolist())


            serialized_output = json.dumps(results)
            return [serialized_output]
        except Exception as e:
            raise RuntimeError("Error during postprocessing") from e

    def handle(self, data, context):
        try:
            # Preprocess the data
            image_tensor, pixel_mask_tensor = self.preprocess(data)

            # Perform inference
            output = self.inference(image_tensor, pixel_mask_tensor)

            # Postprocess the output
            result = self.postprocess(output)

            return result
        except Exception as e:
            print(f"Error in handle method: {e}")
            raise RuntimeError("Error in handle method") from e



"""
with open('detr_model/handler.py', 'w') as f:
    f.write(handler_py)


