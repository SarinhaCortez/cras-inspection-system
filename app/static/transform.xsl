<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:template match="YourReport">
    <html>
      <head>
        <style>
          body {
              font-family: Arial, sans-serif;
          }
          h1 {
              color: navy;
              text-align: center;
          }
          table {
              width: 100%;
              border-collapse: collapse;
          }
          th, td {
              border: 1px solid #000;
              padding: 8px;
              text-align: left;
          }
          th {
              background-color: #f2f2f2;
          }
        </style>
        </head>
      <body>
        <h1>Your prediction at <xsl:value-of select="Date"/>, <xsl:value-of select="Time"/></h1>
        <h2>Image Predictions</h2>

        <xsl:apply-templates select="Image[count(Prediction) > 0]">
          <xsl:sort select="Filename" order="ascending"/> <!-- Sort by filename -->
        </xsl:apply-templates>

        <xsl:if test="count(Image[count(Prediction) = 0]) > 0">
          <h2>No Defects Found</h2>
          <ol>
            <xsl:apply-templates select="Image[count(Prediction) = 0]">
              <xsl:sort select="Filename" order="ascending"/> <!-- Sort by filename -->
            </xsl:apply-templates>
          </ol>
        </xsl:if>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="Image[count(Prediction) > 0]">
    <p><strong>Filename: </strong><xsl:value-of select="Filename" /></p>
    
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
          <xsl:sort select="score" order="descending"/>
          <tr>
            <td><xsl:value-of select="Label" /></td>
            <td><xsl:value-of select="Score" /></td>
            <td><xsl:value-of select="Box" /></td>
          </tr>
        </xsl:for-each>
      </tbody>
    </table>
  </xsl:template>

  <xsl:template match="Image[count(Prediction) = 0]">
    <li><xsl:value-of select="Filename" /></li>
  </xsl:template>

</xsl:stylesheet>
