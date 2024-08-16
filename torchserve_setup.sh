pip install torchserve torch-model-archiver torch-workflow-archiver torch transformers torchvision safetensors pytorch-lightning timm
mkdir -p detr_model model_store
python3 write.py
mv model.safetensors ex_model/model.safetensors
torch-model-archiver --model-name detr --version 1.0 --model-file ex_model/model.py --serialized-file ex_model/model.safetensors --handler ex_model/handler.py --export-path model_store --force
torchserve --start --ncs --model-store model_store --models detr=model_store/detr.mar --ts-config config.properties --disable-token-auth

