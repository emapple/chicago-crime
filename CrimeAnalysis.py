import numpy as np
import matplotlib.pyplot as plt

def convert_time(string):
    temp1 = string.split()
    date = temp1[0]
    temp2 = temp1[1].split(':')
    if temp1[2]=='AM' and temp2[0]!='12':
        minutes = int(temp2[0])*60+int(temp2[1])
    elif temp1[2]=='AM' and temp2[0]=='12':
        minutes = int(temp2[1])
    elif temp1[2]=='PM' and temp2[0]!='12':
        minutes = (12+int(temp2[0]))*60+int(temp2[1])
    elif temp1[2]=='PM' and temp2[0]=='12':
        minutes = 12*60+int(temp2[1])
    else:
        print 'error in minute calculation'
        print temp1
    temp3 = temp1[0].split('/')
    date = (int(temp3[0]), int(temp3[1]), int(temp3[2]))
    return (date,minutes)

def convert_bool(string):
    if string=='false':
        return False
    elif string=='true':
        return True
    else:
        print string
        return -1

if __name__=='__main__':
    
    crime_type = 'HOMICIDE'
    count = 0
    skip_count = 0
    count2017 = 0
    ID = []
    date = [] # (month, day, year)
    time = [] # minute of day (out of 1440)
    primarytype = []
    arrest = []
    location = [] # Latitude, Longitude
    with open('datasets/Crimes_-_2001_to_present.csv','r') as f:
        for line in f:
            if line.startswith('ID'):
                h=line.split(',')
                CONST_LENGTH=len(h)
            if not line.startswith('ID'):
                h=line.split(',')
                if h[-2]!='' and h[-3]!='':
                    good_data = True
                    # taking care of cases where description is, e.g., ' "A, B, C" '
                    for i in range(CONST_LENGTH-2):
                        try:
                            if h[i].startswith('"'):
                                h[i]=h[i].split('"')[-1]
                                while(True):
                                    h[i]=h[i]+h[i+1]
                                    del(h[i+1])
                                    if '"' in h[i]:
                                        h[i] = h[i].split('"')[0]
                                        break
                        except:
                            good_data = False

                    if(good_data):
                        dt=convert_time(h[2])
                        if dt[0][2] <= 2016:
                            arrest.append(convert_bool(h[8]))
                            location.append((float(h[-4]),float(h[-3])))
                            ID.append(int(h[0]))
                            date.append(dt[0])
                            time.append(dt[1])
                            primarytype.append(h[5])
                            count+=1
                        else:
                            count2017+=1
                    else:
                        print 'skip1'
                        skip_count+=1
                else:
                    skip_count+=1
            #if count>100000:
            #    break
    
    print 'count is {}'.format(count)
    print 'skip_count is {}'.format(skip_count)
    print 'count2017 is {}'.format(count2017)

    ID = np.array(ID)
    date = np.array(date)
    time = np.array(time)
    primarytype = np.array(primarytype)
    arrest = np.array(arrest)
    location = np.array(location)

    #print ID
    #print '\n'
    #print date
    #print '\n'
    #print time
    #print '\n'
    #print primarytype 
    #print '\n'
    #print arrest
    #print '\n'
    #print location

    
    phasetable = [[],[],[],[]]
    with open('datasets/moonphase.txt','r') as f:
        for line in f:
            h = line.split()
            dt = h[1].split('/')
            phasetable[0].append(float(dt[0]))
            phasetable[1].append(float(dt[1]))
            phasetable[2].append(float('20'+dt[2]))
            phasetable[3].append(float(h[0]))
    
    phasetable = np.array(phasetable)


    phase = []
    for i in range(len(date)):
        month = date[i, 0]
        day = date[i, 1]
        year = date[i, 2]
        index = np.where((phasetable[0]==month) & (phasetable[1]==day) & (phasetable[2]==year))[0][0]
        phase.append(phasetable[3, index])
    
    phase = np.array(phase)
    
    hts, edgs = np.histogram(phasetable[3], bins=20)
    illum_ws = 1./hts
    #print hts
    #print illum_ws

    allheights, alledges = np.histogram(phase, bins=20, density=True)
    someheights, someedges = np.histogram(phase[np.where(primarytype==crime_type)], bins=20, density=True)
    #print allheights
    #print someheights
    allheights *= illum_ws
    someheights *= illum_ws
    #print allheights
    #print someheights

    plt.figure()
    #plt.scatter(location[:,1],location[:,0],s=1)
    plt.hexbin(location[location[:,1]>-90,1],location[location[:,1]>-90,0],cmap='magma')

    print 'Out of {} crimes, {} were '.format(len(primarytype),len(primarytype[primarytype==crime_type]))+crime_type
    plt.figure()
    #plt.scatter(location[np.where(primarytype==crime_type),1],location[np.where(primarytype==crime_type),0],s=1)
    plt.hexbin(location[(primarytype==crime_type) & (location[:,1]>-90),1],location[(primarytype==crime_type) & (location[:,1]>-90),0],cmap='magma')

    plt.figure()
    plt.hist(date[:,0],bins=np.arange(.5,12.5,1),normed=True,histtype='step',label='All')
    plt.hist(date[np.where(primarytype==crime_type),0][0],bins=np.arange(.5,12.5,1),normed=True,histtype='step',label=crime_type)
    plt.xlabel('Month')
    plt.ylabel('Crimes [Normalized]')
    plt.legend(loc=8)

    plt.figure()
    plt.hist(date[:,1],bins=np.arange(.5,31.5,1),normed=True,histtype='step',label='All')
    plt.hist(date[np.where(primarytype==crime_type),1][0],bins=np.arange(.5,31.5,1),normed=True,histtype='step',label=crime_type)
    plt.xlabel('Day')
    plt.ylabel('Crimes [Normalized]')
    plt.legend(loc=8)

    plt.figure()
    plt.hist(date[:,2],bins=np.arange(2000.5,2018.5,1),normed=True,histtype='step',label='All')
    plt.hist(date[np.where(primarytype==crime_type),2][0],bins=np.arange(2000.5,2018.5,1),normed=True,histtype='step',label=crime_type)
    plt.xlabel('Year')
    plt.ylabel('Crimes [Normalized]')
    plt.legend(loc=8)

    plt.figure()
    plt.hist(time/60.,bins=24,normed=True,histtype='step',label='All')
    plt.hist(time[np.where(primarytype==crime_type)]/60.,bins=24,normed=True,histtype='step',label=crime_type)
    plt.xlabel('Time of Day')
    plt.ylabel('Crimes [Normalized]')
    plt.xlim([0,24])
    plt.legend(loc=8)

    
    plt.figure()
    #plt.hist(phase, bins=20, normed=True, weights=illum_ws, histtype='step',label='All')
    #plt.hist(phase[np.where(primarytype==crime_type)], bins=20, normed=True, weights=illum_ws, histtype='step', label=crime_type)
    plt.step([(alledges[i+1]+alledges[i])*0.5 for i in range(len(alledges)-1)], allheights, 'o', label='All')
    plt.step([(someedges[i+1]+someedges[i])*0.5 for i in range(len(someedges)-1)], someheights, 'o', label=crime_type)
    plt.xlabel('Moon Illumination Fraction')
    plt.ylabel('Crimes [Normalized]')
    plt.xlim([0,1])
    plt.legend(loc=8)


    plt.show()
