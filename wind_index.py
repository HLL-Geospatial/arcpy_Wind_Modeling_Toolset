import arcpy
import math
import regex as re
#import major_interface


from arcpy.sa import *
from arcpy import env

arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True
receptor = arcpy.GetParameterAsText(0)
winddir = arcpy.GetParameterAsText(1)
windspd = arcpy.GetParameterAsText(2)
rec_x = arcpy.GetParameterAsText(3)
rec_y = arcpy.GetParameterAsText(4)
pollution = arcpy.GetParameterAsText(5)
pol_x = arcpy.GetParameterAsText(6)
pol_y = arcpy.GetParameterAsText(7)
dist_thresh = arcpy.GetParameter(8)
output = arcpy.GetParameterAsText(9)
ws = arcpy.GetParameterAsText(10)

arcpy.workspace = output
dist_thresh = int(dist_thresh) * 1000
def get_distance(a,b):
    return math.sqrt((a[0]-b[0])**2+(a[1]-b[1])**2)



def get_angle(a,b):
	#a for the receptor and b for the pollution source
    vertical=b[1]-a[1]
    horizontal=b[0]-a[0]
    angle=0
    if(vertical>=0 and horizontal>=0):
        angle = math.atan( vertical/horizontal )
    elif(vertical>=0 and horizontal<0):
        angle = math.pi + math.atan(vertical/horizontal)
    elif(vertical<0 and horizontal>0):
        angle = 2*math.pi + math.atan(vertical/horizontal)
    else:
        angle= math.pi + math.atan(vertical/horizontal)
    return angle*180/math.pi

def get_GEODESIC_angle(angle):
    if(angle>=0.0 and angle<=90.0):
        return 90-angle
    elif(angle<=180.0):
        return 90-angle
    elif(angle<=270.0):
        return 90-angle
    else:
        return 450-angle

'''
w1: with distance without scale
w2: with distance with scale
w3: without distance with scale
w4: without distance without scale
'''

arcpy.AddMessage('read in wind and pollution data')
wind=arcpy.da.SearchCursor(receptor,[winddir,windspd])
locations_receptor=arcpy.da.SearchCursor(receptor,[rec_x,rec_y])
locations_pollution=arcpy.da.SearchCursor(pollution,[pol_x,pol_y])
wind_directions=[]
wind_speeds=[]
coordinates_receptor=[]
coordinates_pollution=[]

for row in wind:
    wind_directions.append(row[0])
    wind_speeds.append(row[1])

for each in locations_receptor:
    coordinates_receptor.append(each)

for each in locations_pollution:
    coordinates_pollution.append(each)

min_speed=min(wind_speeds)
if(min_speed==0):
    min_speed = 1
for i in range(len(wind_speeds)):
    wind_speeds[i]=wind_speeds[i]/min_speed
if re.match('.*[wW]1.*', ws):
    arcpy.AddMessage('Calculating wind index with distance without scale')
    weights_with_distance_without_scale=[]
    for i in range(len(wind_directions)):
        beta=wind_directions[i]
        result=0
        for j in range(len(coordinates_pollution)):
            distance=get_distance(coordinates_receptor[i],coordinates_pollution[j])
            if distance > dist_thresh:
                continue
            else:		
                alpha = get_angle(coordinates_receptor[i],coordinates_pollution[j])
                if(i==1 and j==5):
                    print(coordinates_receptor[1])			
                    print(coordinates_pollution[5])			
                    print(alpha)		
                cos_value=math.cos(math.radians(180+get_GEODESIC_angle(alpha)-beta))
                #added on April 25th for NaN value bugs		
                if(math.isnan(cos_value) or math.isnan(distance)):			
                    print("get a NaN value from data, ignore this entry!")			
                    continue
                #end of addition		

            result=result+(1-cos_value)/(2*distance)	

        weights_with_distance_without_scale.append(math.sqrt(result))
            
    arcpy.AddMessage('writing the result to: '+ receptor)	
    #write the result to the receptor table
    arcpy.AddField_management(receptor,'w1','Double')

    with arcpy.da.UpdateCursor(receptor, 'w1') as cursor:		
        count=0			
        for row in cursor:				
            row[0]=weights_with_distance_without_scale[count]				
            count+=1				
            cursor.updateRow(row)	

    IDW_w1 = Idw(receptor, "w1")
    IDW_w1.save(output + '\\wI_w2.tif')
    W1_fuzzy = FuzzyMembership(IDW_w1,FuzzyLarge())
    W1_fuzzy.save(output+'\\WI_w1_fz.tif')
if re.match('.*[wW]2.*', ws):		
    arcpy.AddMessage('Calculating wind index with distance with scale')		
    weights_with_distance_with_scale=[]		
    for i in range(len(wind_directions)):			
        beta=wind_directions[i]			
        result=0			
        for j in range(len(coordinates_pollution)):				
            distance=get_distance(coordinates_receptor[i],coordinates_pollution[j]) # An if statement checking the distance as opposed to threshold would be good here				
            if distance > dist_thresh:
                continue

            else:
                alpha = get_angle(coordinates_receptor[i],coordinates_pollution[j])				
                cos_value=math.cos(math.radians(180+get_GEODESIC_angle(alpha)-beta))

                    #added on April 25th for NaN value bugs				
                if(math.isnan(cos_value) or math.isnan(distance)):					
                    print("get a NaN value from data, ignore this entry!")					
                    continue
                    #end of addition				
                if(cos_value<0):					
                    result=result+wind_speeds[i]*(1-cos_value)/(2*distance)				
                else:					
                    result=result+(1-cos_value)/(2*distance)
                if result < 0:
                    result = 0
        	        
        weights_with_distance_with_scale.append(math.sqrt(result))	    
    arcpy.AddMessage('writing the result to: '+receptor)	
            #write the result to the receptor table
            
    arcpy.AddField_management(receptor,'w2','Double')		
    with arcpy.da.UpdateCursor(receptor, 'w2') as cursor:			
        count=0			
        for row in cursor:				
            row[0]=weights_with_distance_with_scale[count]				
            count+=1				
            cursor.updateRow(row)	

    IDW_w2 = Idw(receptor, "w2")
    W2_fuzzy = FuzzyMembership(IDW_w2,FuzzyLarge())
    W2_fuzzy.save(output+'\\WI_w2_fz.tif')
    IDW_w2.save(output + '\\WI_ws.tif')
#		'''		
#		self.update('Interpolation for wind index with distance with scale')
#		out_directory = self.output+'/wdws_IDW'
#		arcpy.gp.Idw_sa(self.receptor, "w2", out_directory, "30", "2", "VARIABLE 12", "")
#
#		self.update('Fuzzy for wind index with distance with scale')
#		out_directory_fuzzy = self.output+'/wdws_fuzzy'
#		arcpy.gp.FuzzyMembership_sa(out_directory,out_directory_fuzzy,"LARGE 2 10", "NONE")
#		'''	
if re.match('.*[wW]3.*', ws):	
    arcpy.AddMessage('Calculating wind index without distance with scale')		
    weights_no_distance_with_scale=[]		
    for i in range(len(wind_directions)):			
        beta=wind_directions[i]			
        result=0			
        for j in range(len(coordinates_pollution)):				
            distance=1				
            alpha = get_angle(coordinates_receptor[i],coordinates_pollution[j])				
            cos_value=math.cos(math.radians(180+get_GEODESIC_angle(alpha)-beta))

                    #added on April 25th for NaN value bugs
                    
            if(math.isnan(cos_value) or math.isnan(distance)):					
                print("get a NaN value from data, ignore this entry!")					
                continue
                    #end of addition				
            if(cos_value<0):					
                result=result+wind_speeds[i]*(1-cos_value)/(2*distance)				
            else:					
                result=result+(1-cos_value)/(2*distance)
            if result < 0:
                result = 0			
        weights_no_distance_with_scale.append(math.sqrt(result))
            
    arcpy.AddMessage('writing the result to: '+receptor)
            #write the result to the receptor table
            
    arcpy.AddField_management(receptor,'w3','Double')		
    with arcpy.da.UpdateCursor(receptor, 'w3') as cursor:			
        count=0			
        for row in cursor:				
            row[0]=weights_no_distance_with_scale[count]				
            count+=1				
            cursor.updateRow(row)	
        
    IDW_w3 = Idw(receptor, "w3")
    IDW_w3.save(output + '\\WI_w3.tif')
    W3_fuzzy = FuzzyMembership(IDW_w3,FuzzyLarge())
    W3_fuzzy.save(output+'\\WI_w3_fz')	
#		'''		
#		self.update('Interpolation for wind index without distance with scale')
#		out_directory = self.output+'/ndws_IDW'
#		arcpy.gp.Idw_sa(self.receptor, "w3", out_directory, "30", "2", "VARIABLE 12", "")
#
#		self.update('Fuzzy for wind index without distance with scale')
#		out_directory_fuzzy = self.output+'/ndws_fuzzy'
#		arcpy.gp.FuzzyMembership_sa(out_directory,out_directory_fuzzy,"LARGE 2 10", "NONE")
#		'''		
if re.match('.*w4.*', ws):
    arcpy.AddMessage('Calculating wind index without distance without scale')		
    weights_no_distance_without_scale=[]		
    for i in range(len(wind_directions)):			
        beta=wind_directions[i]			
        result=0			
        for j in range(len(coordinates_pollution)):				
            distance=1				
            alpha = get_angle(coordinates_receptor[i],coordinates_pollution[j])				
            cos_value=math.cos(math.radians(180+get_GEODESIC_angle(alpha)-beta))
                    #added on April 25th for NaN value bugs				
            if(math.isnan(cos_value) or math.isnan(distance)):					
                print("get a NaN value from data, ignore this entry!")					
                continue
                    #end of addition				
            result=result+(1-cos_value)/(2*distance)
            if result < 0:
                result = 0			
        weights_no_distance_without_scale.append(math.sqrt(result))
    arcpy.AddMessage('writing the result to: '+receptor)
            #write the result to the receptor table		
    arcpy.AddField_management(receptor,'w4','Double')		
    with arcpy.da.UpdateCursor(receptor, 'w4') as cursor:			
        count=0			
        for row in cursor:				
            row[0]=weights_no_distance_without_scale[count]				
            count+=1				
            cursor.updateRow(row)	
            
    IDW_w4 = Idw(receptor, "w4")
    IDW_w4.save(output + '\\WI_w4.tif')
    W4_fuzzy = FuzzyMembership(IDW_w4,FuzzyLarge())
    W4_fuzzy.save(output+'\\WI_w4_fz.tif')	
		
#		'''
#		self.update('Interpolation for wind index without distance without scale')
#		out_directory = self.output+'/ndns_IDW'
#		arcpy.gp.Idw_sa(self.receptor, "w4", out_directory, "30", "2", "VARIABLE 12", "")
#
#		self.update('Fuzzy for wind index without distance without scale')
#		out_directory_fuzzy = self.output+'/ndns_fuzzy'
#		arcpy.gp.FuzzyMembership_sa(out_directory,out_directory_fuzzy,"LARGE 2 10", "NONE")
#		'''

arcpy.AddMessage('wind index processing DONE')
        

