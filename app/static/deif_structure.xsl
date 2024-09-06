<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <!-- Template for the root element -->
  <xsl:template match="YourReport">
    <html>
      <body>
        <h1>Your prediction at <xsl:value-of select="Date"/>, <xsl:value-of select="Time"/></h1>
        <h2>Image Predictions</h2>

        <!-- Apply templates to images, sorting images first by whether they have predictions and then by filename -->
        <xsl:apply-templates select="Image">
          <xsl:sort select="count(Prediction)" order="descending"/> <!-- Images with predictions come first -->
          <xsl:sort select="Filename" order="ascending"/> <!-- Sort by filename within the group -->
        </xsl:apply-templates>
      </body>
    </html>
  </xsl:template>

  <!-- Template for each Image -->
  <xsl:template match="Image">
    <p><strong>Filename: </strong><xsl:value-of select="Filename" /></p>
    
    <!-- Check if there are Prediction elements -->
    <xsl:choose>
      <xsl:when test="count(Prediction) > 0">
        <!-- If there are predictions, show the table -->
        <table>
          <thead>
            <tr>
              <th>Label</th>
              <th>Score</th>
              <th>Box (X, Y, Width, Height)</th>
            </tr>
          </thead>
          <tbody>
            <xsl:for-each select="Prediction">
              <xsl:sort select="Label" order="ascending"/>
              <tr>
                <td><xsl:value-of select="Label" /></td>
                <td><xsl:value-of select="Score" /></td>
                <td><xsl:value-of select="Box" /></td>
              </tr>
            </xsl:for-each>
          </tbody>
        </table>
      </xsl:when>

      <!-- If there are no predictions, print "NO DEFECTS FOUND" -->
      <xsl:otherwise>
        <p><strong>NO DEFECTS FOUND</strong></p>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

</xsl:stylesheet>
