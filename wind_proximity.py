import arcpy
import math
#import major_interface
import time
import os
from arcpy.sa import *
from arcpy import env


#### Code works to print out Proximity and Fuzzy Proximity
#### Will need to continue testing the size portion


arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

arcpy.AddMessage('Start at 2021')

receptor = arcpy.GetParameterAsText(0)
rec_x = arcpy.GetParameterAsText(1)
rec_y = arcpy.GetParameterAsText(2)
pollution = arcpy.GetParameterAsText(3)
pol_x = arcpy.GetParameterAsText(4)
pol_y = arcpy.GetParameterAsText(5)
Pollution_area = arcpy.GetParameterAsText(6)
Dist_tre = arcpy.GetParameterAsText(7)

output = arcpy.GetParameterAsText(8)

arcpy.AddMessage('Start')

if len(Dist_tre)>0:    
    Dist_tre = float(Dist_tre) * 1000    
else:
    Dist_tre = 50000000

arcpy.workspace = output

def get_distance(a,b):
	return math.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)

torf = False
if len(Pollution_area)>0:
    Sum_size= 0
    with arcpy.da.SearchCursor(pollution, Pollution_area) as cursor:			
        for row in cursor:
            Sum_size = Sum_size + row[0] # Get the sum of the sizes in all the pollution sources				
    arcpy.AddWarning(Sum_size)
    
    arcpy.AddField_management(pollution,'SqtA_new','Double')
    with arcpy.da.UpdateCursor(pollution, [Pollution_area,'SqtA_new']) as cursor:
        for row1 in cursor:
            row1[1] = math.sqrt(row1[0]/Sum_size) # get the square root of each pollution area over the sum of all the pollution areas
            cursor.updateRow(row1)
    cursors_areas = arcpy.da.SearchCursor(pollution,['SqtA_new'])		
    torf = True
		
arcpy.AddMessage('read in receptor and pollution data')
# Get the pollution locations as a search cursor
cursors_pollutions = arcpy.da.SearchCursor(pollution,[pol_x,pol_y])

		#change on 2021/4/24 for data without size information
total_length = 0
for each in cursors_pollutions:
    total_length += 1
print('****: total_length  ', total_length)		
#pollution_size = []
cursors_FID = arcpy.da.SearchCursor(receptor,['FID'])		
cursors_receptors = arcpy.da.SearchCursor(receptor,[rec_x,rec_y])

if torf == True:
    areas_pollution = []
    for each in cursors_areas: # get a list of all the square roots of the area fractions			
        areas_pollution.append(each)

    weights=[]		
    for each in areas_pollution: # Get the same as above, but not in a list 			
        weights.append(each[0])
locations_pollution=[]		
locations_receptor=[]		
areas_pollution=[]		
FID = []		
IN_FID=[]

		
cursors_pollutions = arcpy.da.SearchCursor(pollution,[pol_x,pol_y])	
# makes a list of all the seperate pollution and receptor info	
for each in cursors_pollutions:			
    locations_pollution.append(each)

for each in cursors_receptors:			
    locations_receptor.append(each)

for each in cursors_FID:			
    FID.append(each)
					
arcpy.AddMessage('Calculating proximity')		
index = []
index1 = []	

	
for i in range(len(locations_receptor)): # Run through the x,y locations of each receptor			
    result=0		
    
    for j in range(len(locations_pollution)):  # Run through the x,y locations of each pollution source
    
        dis_r_p = get_distance(locations_receptor[i],locations_pollution[j]) # get the distance between each receptor and pollution source
        if dis_r_p <= Dist_tre: # Evaluate each distance against the distance threshold
            temp = (1/dis_r_p) # get the inverse weight of the receptor/pollutant distance 
        else:
            temp = 0 # If the distance is above the threshold, temp = 0
                		
        if(math.isnan(temp)): # double check that temp is a number
            continue
        if torf:
            arcpy.AddMessage('Calculating Size')
            result1 = 0	
            for j in range(len(weights)):
                dis_r_p = get_distance(locations_receptor[i],locations_pollution[j])
                if dis_r_p <= Dist_tre:
                    temp1 = (weights[j]/dis_r_p)    
                else:
                    temp1 = 0        		
        
                if(math.isnan(temp1)):
                    continue
        
                result1 = result1+temp1
    
            result1 = math.sqrt(result1)
    
            index1.append(result1)
        result = result+temp # Result is the addition of temp + result
    result=math.sqrt(result) # get the square root of the result
    
    index.append(result) # append index to result
    
		
arcpy.AddMessage('writing the result to: '+receptor)
		#add field of wind priximity
arcpy.AddField_management(receptor,'New_Prox','Double')

with arcpy.da.UpdateCursor(receptor, ['New_Prox']) as cursor:			
    count=0			
    for row in cursor: # run through the receptor file to update it 				
        row[0]=index[count]	 # each New_Prox will be equal to the index value for the same receptor 	
        #row[1]=index1[count]		
        count+=1				
        cursor.updateRow(row)	
# Create the IDW and fuzzy IDW
IDW_out = Idw(receptor, "New_Prox")
out_fuzzy = FuzzyMembership(IDW_out,FuzzyLarge())

out_fuzzy.save(output+'\\Proximity_fz.tif')
IDW_out.save(output + '\\Proximity.tif')
arcpy.AddMessage('wind proximity processing DONE')
arcpy.AddField_management(receptor,'Prox_size','Double')

if torf:
    with arcpy.da.UpdateCursor(receptor, ['Prox_size']) as cursor:			
        count=0			
        for row in cursor:				
            row[0]=index1[count]		
            #row[1]=index1[count]		
            count+=1				
            cursor.updateRow(row)
    IDW_out1 = Idw(receptor, "Prox_size")
    out_fuzzy1 = FuzzyMembership(IDW_out1,FuzzyLarge())
    out_fuzzy1.save(output+'\\Prox_size_fz.tif')
    IDW_out1.save(output + '\\Prox_size.tif')	
# # the above is done again if there's a pollution_area field? 
# if len(Pollution_area)>0:
#     Sum_size= 0
#     with arcpy.da.SearchCursor(pollution, Pollution_area) as cursor:			
#     #count=0			
#         for row in cursor:
#             Sum_size = Sum_size + row[0] # Get the sum of the sizes in all the pollution sources				
#     arcpy.AddWarning(Sum_size)
    
#     arcpy.AddField_management(pollution,'SqtA_new','Double')
#     with arcpy.da.UpdateCursor(pollution, [Pollution_area,'SqtA_new']) as cursor:
#         for row1 in cursor:
#             row1[1] = math.sqrt(row1[0]/Sum_size) # get the square root of each pollution area over the sum of all the pollution areas
#             cursor.updateRow(row1)
            
#     cursors_areas = arcpy.da.SearchCursor(pollution,['SqtA_new'])		
    
#     for each in cursors_areas: # get a list of all the square roots of the area fractions			
#         areas_pollution.append(each)

#     weights=[]		
#     for each in areas_pollution: # Get the same as above, but not in a list 			
#         weights.append(each[0])
       
#     index1 = []
#     # This is redone?
#     for i in range(len(locations_receptor)):			
#         result1 = 0	
#         for j in range(len(weights)):
#             dis_r_p = get_distance(locations_receptor[i],locations_pollution[j])
#             if dis_r_p <= Dist_tre:
#                 temp1 = (weights[j]/dis_r_p)    
#             else:
#                 temp1 = 0        		
        
#             if(math.isnan(temp1)):
#                 continue
        
#             result1 = result1+temp1
    
#         result1 = math.sqrt(result1)
    
#         index1.append(result1)
    
#     arcpy.AddField_management(receptor,'Prox_size','Double')
#     with arcpy.da.UpdateCursor(receptor, ['Prox_size']) as cursor:			
#         count=0			
#         for row in cursor:				
#             row[0]=index1[count]		
#         #row[1]=index1[count]		
#             count+=1				
#             cursor.updateRow(row)	
        
#     IDW_out1 = Idw(receptor, "Prox_size")
#     out_fuzzy1 = FuzzyMembership(IDW_out1,FuzzyLarge())
#     out_fuzzy1.save(output+'\\Prox_size_fz.tif')
#     IDW_out1.save(output + '\\Prox_size.tif')