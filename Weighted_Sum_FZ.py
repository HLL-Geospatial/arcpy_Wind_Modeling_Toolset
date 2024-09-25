import arcpy
from arcpy import env
from arcpy.sa import *



arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True
Input = arcpy.GetParameterAsText(0)
output = arcpy.GetParameterAsText(1)


Input = Input.split(';')
Raster_no = len(Input)
weight = []
raster_path = []
Out_raster = 0
#output = output_folder + '\\TWE_FZ'

for i in Input:
    input1 = i.split(' ')
    weight.append(float(input1[2]))
    raster_path.append(input1[0])
if sum(weight) != 1:
    arcpy.AddError('Error, the weights should add up to 1!')
else:
    for j in range(Raster_no):
        Out_raster = Out_raster + weight[j]*Raster(raster_path[j])
    Out_raster.save(output)
#arcpy.AddWarning(weight)
#arcpy.AddWarning(raster_path)
#Out_raster.save(output)

#arcpy.gp.FuzzyMembership_sa(out_directory,out_directory_fuzzy,"LARGE 2 10", "NONE")




