import arcpy
from arcpy.sa import *
import numpy as np
from arcpy import env

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True
Input = arcpy.GetParameterAsText(0)
output_folder = arcpy.GetParameterAsText(1)

#Wind_index = arcpy.GetParameterAsText(0)
#Wind_index_W = arcpy.GetParameterAsText(1)
#Wind_prox = arcpy.GetParameterAsText(2)
#Wind_prox_W = arcpy.GetParameterAsText(3)
#TWE = arcpy.GetParameterAsText(4)
#TWE_W =  arcpy.GetParameterAsText(5)
#Landform = arcpy.GetParameterAsText(6)
#Landform_W =  arcpy.GetParameterAsText(7)
#Target_V = arcpy.GetParameterAsText(8)
#Folder = arcpy.GetParameterAsText(9)

arcpy.env.workspace = output_folder



#def get_weights(R1,wind_index,R2,proximity,R3,landform,R4,TWE,variate):
def get_weights(Input,output):   
    Input = Input.split(';')
    Raster_no = len(Input)
    weight = []
    raster_path = []
    
    
    
    
    for ii in Input:
        input1 = ii.split(' ')
        weight.append(float(input1[2]))
        raster_path.append(input1[0])
    if sum(weight) != 1:
        arcpy.AddError('Error, the weights should add up to 1!')
        quit()
    for j in range(Raster_no):
        arcpy.AddWarning('Runing sensitivity analysis for ' + raster_path[j])
        initial=0
        num_s = 0
        num_m = 0
        num_l = 0
        per_s = []
        per_m = []
        per_l = []
        w_value = []
        
        if (weight[j]>0.2):
            initial = weight[j]-0.2
        if (weight[j]>=0.8):
            initial = 0.59
        for i in range(41):
            inmess = 'round ' + str(i) + ' start'
            arcpy.AddMessage(inmess)
            temp = [0]*Raster_no
            
            temp[j] = initial
            R = 0
            
            for k in range(1,Raster_no):
                temp[(j+k) % Raster_no] = (1-initial) * (weight[(j+k) % Raster_no]/(1-weight[j]))
            initial += 0.01
            for jj in range(Raster_no):
                R = R + temp[jj]*Raster(raster_path[jj])
            arcpy.AddMessage('finished calculating weighted sum')
            v_max = float(arcpy.GetRasterProperties_management(R,'MAXIMUM')[0])
            v_min = float(arcpy.GetRasterProperties_management(R,'MINIMUM')[0])
            arcpy.AddMessage('reading properties of raster')
            Tri_1 = (v_max-v_min)/3+v_min
            Tri_2 = Tri_1 + (v_max-v_min)/3

            Tri_s = Con(R<=Tri_1,1,0)
            Tri_m = Con(((R>Tri_1) & (R<=Tri_2)),1,0)
            Tri_l = Con(R>Tri_2,1,0)
            arcpy.AddMessage('getting three raster: small\medium\large')
            arcpy.AddMessage('Calculating the persentage')
        
            arcpy.MakeRasterLayer_management(Tri_s,'Tri_s')   
            with arcpy.da.SearchCursor('Tri_s',['Value','Count']) as cursor:
                for row in cursor:
                    if row[0] == 1:
                        num_s = row[1]
            arcpy.AddMessage('small finished')

            arcpy.MakeRasterLayer_management(Tri_m,'Tri_m')
            with arcpy.da.SearchCursor('Tri_m',['Value','Count']) as cursor:
                for row in cursor:
                    if row[0] == 1:
                        num_m = row[1]
            arcpy.AddMessage('medium finished')
            
            arcpy.MakeRasterLayer_management(Tri_l,'Tri_l')
            with arcpy.da.SearchCursor('Tri_l',['Value','Count']) as cursor:
                for row in cursor:
                    if row[0] == 1:
                        num_l = row[1]
            arcpy.AddMessage('large finished')
            
            per_s.append(float(num_s)/(num_m+num_s+num_l))
            per_m.append(float(num_m)/(num_m+num_s+num_l))      
            per_l.append(float(num_l)/(num_m+num_s+num_l))
            w_value.append(temp[j])
            
        percent_csv = np.array([w_value,per_s,per_m,per_l])
        outmess = 'round ' + str(i) + ' end'
        arcpy.AddMessage(outmess)
        csv_name = output + '\\' + str(j) + '.csv'
        np.savetxt(csv_name, percent_csv, delimiter=",",fmt = '%s')
        
     
get_weights(Input, output_folder)
