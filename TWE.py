import arcpy
from arcpy import env
from arcpy.sa import *


arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")
Slope = arcpy.GetParameterAsText(0)
winddir = arcpy.GetParameterAsText(1)
aspect = arcpy.GetParameterAsText(2)
output_folder = arcpy.GetParameterAsText(3)


#sql_o = 'Sin(' + Slope + '/57.296) * Cos((' + winddir + '-' + aspect + ')/57.296)'
#arcpy.gp.RasterCalculator_sa(sql_o,output)
TWE = output_folder + '\\TWE'
TWE_fz = output_folder + '\\TWE_FZ'

Out_raster = Sin(Raster(Slope)/57.296)*Cos((Raster(winddir)-Raster(aspect))/57.296)
arcpy.AddWarning(TWE)
Out_raster.save(TWE)
Input_fuzzy = Out_raster + 1
#arcpy.gp.Idw_sa(fz_raster, "w4", out_directory, "30", "2", "VARIABLE 12", "")
Out_fuzzy = FuzzyMembership(Input_fuzzy,FuzzyLarge())
Out_fuzzy.save(TWE_fz)



