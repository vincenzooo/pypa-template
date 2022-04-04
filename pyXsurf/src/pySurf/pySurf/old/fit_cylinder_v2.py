import numpy as np
from scipy.optimize import minimize
from pySurf.points import *
import mpl_toolkits.mplot3d as m3d
from pyGeneralRoutines.fn_add_subfix import fn_add_subfix

def closest_point_on_line(points,lVersor,lPoint):
    """From a list of points in 3D space as Nx3 array, returns a Nx3 array with the corresponding closest points on the line."""
    vd=lVersor/((np.array(lVersor)**2).sum())  #normalize vector, not sure it is necessary.
    return lPoint+(points-lPoint).dot(vd)[:,np.newaxis]*(vd)

    
def cylinder_error(odr=(0,0,0,0,0,0),points=None,extra=False):  #origin=(0,0,0),direction=(0,1.,0),radius is calculated from best fit
    """Given a set of N points in format Nx3, returns the   error on the cylinder defined by origin and direction as a 6(3+3) dim vector.
    If extra is set, additional values are returned :
        radius: best fit radius for the cylinder.
        deltaR[N,3]: deviation from radius for each point."""
    
    #ca 400 ms per loop
    origin=odr[0:3]
    direction=odr[3:]
    vd=direction/((np.array(direction)**2).sum())  #normalize vector, not sure it is necessary.
    x,y,z=np.hsplit(points,3)
    Paxis=closest_point_on_line(points,direction,origin) #points on the cylinder axis closer to points to fit
    deltaR2=((points-Paxis)**2).sum(axis=1)-radius**2  #square difference from expected radius for each point
    fom=np.sqrt(deltaR2.sum()/len(deltaR2))
    if extra:
        residuals=np.hstack([x,y,deltaR[:,None]])
        return fom,residuals,radius
    else: return fom  #,deltaR,radius   

def cylinder_error3(odr=(0,0,0,0),points=None,radius=None,extra=False,xy=False):  
#from v1
#origin=(0,0,0),direction=(0,1.,0),radius is calculated from best fit
    """Given a set of N points in format Nx3, returns the rms surface error on the cylinder defined by origin (intercept of the axis with x=0) and direction, 
    passed as 4-vector odr (origin_y,origin_z,direction_x,direction_z). 
    Best fit radius for odr is calculated as average if not provided. If provided as input it is
        not optimized.
    If extra is set, additional values are returned :
        radius: best fit radius for the cylinder.
        deltaR[N,3]: deviation from radius for each point.
    """
    #2015/08/26 changed sign of deltaR to follow bump up convention (and cone_error3)
    #ca 400 ms per loop
    if xy:
        origin=(0,odr[0],odr[1])
        direction=(1.,odr[2],odr[3])
    else:
        origin=(odr[0],0,odr[1])
        direction=(odr[2],1.,odr[3])
    
    #vd=direction/((np.array(direction)**2).sum())  #normalize vector, not sure it is necessary.
    x,y,z=np.hsplit(points,3)
    Paxis=closest_point_on_line(points,direction,origin)
    #origin+(points-origin).dot(vd)[:,np.newaxis]*(vd) #points on the cylinder axis closer to points to fit
    R=np.sqrt(((points-Paxis)**2).sum(axis=1)) #distance of each point from axis
    if radius is None:
        radius=R.mean()  #
    #plt.plot(R-radius)
    deltaR=(radius-R)  #square difference from expected radius for each point
    fom=np.sqrt(((deltaR)**2).sum()/len(deltaR))
    residuals=np.hstack([x,y,deltaR[:,None]])
    if extra: return fom,residuals,radius
    else: return fom  #,deltaR,radius

def cone_error(odr=(0,0,0,0,0,0),points=None,extra=False):  #origin=(0,0,0),direction=(0,1.,0),radius is calculated from best fit
    """Given a set of N points in format Nx3, returns the rms surface error on the cone defined by origin (intercept of the axis with x=0) and direction, 
    passed as 4-vector odr(origin_y,origin_z,direction_x,direction_z). 
    Best fit cone for odr is calculated from linear fit of data. 
    If extra is set, additional values are returned :
    coeff: best fit radius for the cone as [m,q] for x' distance from x=0 plan on cone axis R(x')=m x' + q. Half cone angle is atan(m). 
    deltaR[N,3]: deviation from radius for each point.
    """
    #ca 400 ms per loop
    origin=odr[0:3]
    direction=odr[3:]
    vd=direction/((np.array(direction)**2).sum())  #normalize vector, not sure it is necessary.
    x,y,z=np.hsplit(points,3)
    Paxis=closest_point_on_line(points,direction,origin)
    Paxdist=np.sqrt(((Paxis-origin)**2).sum(axis=1)) #distance of each point from
    R=np.sqrt(((points-Paxis)**2).sum(axis=1)) #distance of each point from axis
    coeff=np.polyfit(Paxdist,R,1) #best fit cone
    deltaR=R-coeff[0]*Paxdist-coeff[1] #residuals
    fom=np.sqrt(((deltaR)**2).sum()/len(deltaR))
    residuals=np.hstack([x,y,deltaR[:,None]])
    if extra: return fom,residuals,coeff
    else: return fom  #,deltaR,radius

def cone_error3(odr=(0,220.,0,0),points=None,coeff=None,extra=False):
#2015/01/13 changed sign of deltaR to set bump-positive (it was opposite)
#from v1
#origin=(0,0,0),direction=(0,1.,0),radius is calculated from best fit
    """Given a set of N points in format Nx3, returns the rms surface error on the cone defined by 
    its axis (radius and apex are determined by best fit).
    Axis is defined as a 4 elements vector odr=(x,z,cx,cz), not in xz plane.
    origin (intercept of the axis with y=0) and director cosines.
    If coeff is passed as input, the fit for cone surface is not performed and the coeff values are used.
    If extra is set, additional values are returned :
    coeff: best fit radius for the cone as [m,q] for x' distance from x=0 plan on cone axis R(x')=m x' + q. Half cone angle is atan(m). 
    deltaR[N,3]: deviation from radius for each point. Bump positive convention (smaller radius is positive).
    """
    #ca 400 ms per loop
    origin=np.array((odr[0],0,odr[1])) #point of axis at y=0
    direction=np.array((odr[2],np.sqrt(1-odr[2]**2-odr[3]**2),odr[3])) # director cosines, cy is assumed positive
    direction=direction/np.sqrt((direction**2).sum())
    x,y,z=np.hsplit(points,3)
    Paxis=closest_point_on_line(points,direction,origin)
    Paxdist=np.sqrt(((Paxis-origin)**2).sum(axis=1))*np.sign(Paxis[:,1]-origin[1])
 #d: on axis coordinate of points
    R=np.sqrt(((points-Paxis)**2).sum(axis=1)) #r: distance of each point from axis
    if coeff is None:
        coeff=np.polyfit(Paxdist,R,1) #best fit cone
    deltaR=coeff[0]*Paxdist+coeff[1]-R #residuals
    fom=np.sqrt(((deltaR)**2).sum()/len(deltaR))
    residuals=np.hstack([x,y,deltaR[:,None]])
    if extra: return fom,residuals,coeff
    else: return fom  #,deltaR,radius
	
def subtract_cylinder(pp,odr,sampleName=''):
#not used in v1
    """
    odr: 6-vector (origin_y,origin_y,origin_z,direction_x,direction_y,direction_z),
        note that  this is redundant, since only two components are enough for direction 
        (magnitude is irrelevant).
    pp: complete set of points Npx3
    """
    fom,deltaR,radius=cylinder_error(odr,pp,extra=True)
    xymin=np.nanmin(pp,axis=0)[0:2]
    xymax=np.nanmax(pp,axis=0)[0:2]
    rp=plot_points(np.hstack([pp[:,0:2],deltaR[:,None]*1000]),shape=(281,3001)) #this is done to easily replot and change scale

    #surface map and data
    plt.clf()
    plt.imshow(rp,aspect='equal',interpolation='none',vmin=-5,vmax=10,
        extent=[xymin[1],xymax[1],xymin[0],xymax[0]])
    plt.colorbar()
    plt.title(sampleName+(sampleName if sampleName else '')+'best-fit-cylinder removed.')
    plt.xlabel('Y(mm)')
    plt.ylabel('X(mm)')
    plt.savefig(fn_add_subfix(datafile,'_cylinder','png'))
    save_points(np.hstack([pp[:,0:2],deltaR[:,None]*1000]),fn_add_subfix(datafile,'_cylinder'))    
    
    #cylinder output
    print('Best fit radius %s'%radius)
    misal=np.arccos(1/np.sqrt(1+((odr[2:]**2).sum())))
    print('Misalignment of optical axis: %s rad (%s deg)'%(misal,misal*np.pi/180))
    
    #rms output
    print('rms entire surface %s'%(np.nanstd(rp)))
    plt.figure()
    plt.plot(np.nanstd(rp))
    plt.plot(np.nanstd(rp,axis=0))
    plt.plot(np.nanstd(rp,axis=1))

    #mask outliers on a copy
    rp2=rp[:]
    np.where(np.isnan(rp2))

def subtract_cone(pp,odr,sampleName='',outfile=None,vmin=None,vmax=None):
#not used in v1
    """
    odr: 6-vector (origin_y,origin_y,origin_z,direction_x,direction_y,direction_z),
        note that  this is redundant, since only two components are enough for direction 
        (magnitude is irrelevant).
    pp: complete set of points Npx3
    """
    fom,deltaR,coeff=cone_error(odr,pp,extra=True)
    xymin=np.nanmin(pp,axis=0)[0:2]
    xymax=np.nanmax(pp,axis=0)[0:2]
    rp=plot_points(np.hstack([pp[:,0:2],deltaR[:,None]*1000]),shape=(281,3001)) #this is done to easily replot and change scale

    #surface map and data
    plt.clf()
    plt.imshow(rp,aspect='equal',interpolation='none',vmin=vmin,vmax=vmax,
        extent=[xymin[1],xymax[1],xymin[0],xymax[0]])
    plt.colorbar()
    plt.title(((sampleName+' - ') if sampleName else (''))+'best-fit-cone removed.')
    plt.xlabel('Y(mm)')
    plt.ylabel('X(mm)')
    if outfile:
        plt.savefig(fn_add_subfix(outfile,'_cone','png'))
        save_points(np.hstack([pp[:,0:2],deltaR[:,None]*1000]),fn_add_subfix(outfile,'_cone'))    
    
    #cone output
    m=coeff[0]
    print('Cone angle:%s+/-%s rad(%s+/-%s deg) '%(np.arctan(m),0,np.arctan(m)*180/np.pi,0))
    print('Axis intercept at x=0: %smm '%(coeff[1]))
    misal=np.arccos(1/np.sqrt(1+((odr[2:]**2).sum())))
    print('Misalignment of optical axis: %s rad (%s deg)'%(misal,misal*180./pi))
    
    #rms output
    print('rms entire surface %s'%(np.nanstd))
    plt.figure()
    plt.plot(np.nanstd(rp))
    plt.plot(np.nanstd(rp,axis=0))
    plt.plot(np.nanstd(rp,axis=1))

    #mask outliers on a copy
    rp2=rp[:]
    np.where(np.isnan(rp2))   
    return fom,deltaR,coeff
    
def fit_cylinder(points,guessValue=None):
#not used in v1
    if guessValue!=None:
        odr=guessValue
    else:
        odr=(0,220.,0,0)
    result=minimize(cylinder_error,x0=(odr,),args=(points,),options={'maxiter':1000},callback=p,method='Nelder-Mead')
    d=result.x[[2,3]]
    angle=np.arccos()

def fit_cone(points,guessValue=None):
#not used in v1
    if guessValue!=None:
        odr=guessValue
    else:
        odr=(0,220.,0,0)
    result=minimize(cone_error,x0=(odr,),args=(points,),options={'maxiter':1000},callback=p,method='Nelder-Mead')
    d=result.x[[2,3]]
    angle=np.arccos()
    
    
if __name__=='__main__':
    fit_func=cone_error    #this is the function giving the FOM to be minimized
    def p(x): print(x) #,cylinder_error(x,points)
    outSubfix='_cone' #the name of output file is the datafile with this subfix added
    datafile='OP2S04b/04_OP2S04_xyscan_Height_transformed.dat'
    #datafile='OP2S03c/22_OP2S03_yxsurf_Height_transformed.dat'
    #datafile='OP2S04/04_OP2S04_xyscan_Height_transformed.dat'
    #datafile='OP2S05/05_OP2S05_xysurf_Height_transformed.dat'
    

    #create points to be fit from a subset of points.
    pts=get_points(datafile,delimiter=' ')
    #pts=rotate_points(pts,-np.pi/2)
    pts=crop_points(pts,(-28,33),(-75,65))
    pts[:,2]=pts[:,2]/1000.
    c=crop_points(pts,(-28,33),(-50,50))    #[0:-1:1000,:]
    odr2=(33,220.,0,0,220)
    result=minimize(fit_func,x0=(odr2[0:-1],),args=(c,),options={'maxiter':1000},callback=p,method='Nelder-Mead')
    print('-----------------------------------')
    print('Results of fit on subset of points:')
    print(result)    
    
    #create output results applying the value from fit to all points
    odr=result.x
    fom,deltaR,coeff=fit_func(odr,pts,extra=True)
    origin=(odr[0],0,odr[1])
    direction=(odr[2],1.,odr[3])
    deltaR[:,2]=deltaR[:,2]*1000
    print('-----------------------------------')
    print('Results of fit applied to complete set of points:')
    print('F.O.M.=%s'%(fom))
    
    plot_points(deltaR,vmin=-5,vmax=10,scatter=1,aspect='equal')
    save_points(deltaR,filename=fn_add_subfix(datafile,outSubfix))
    plt.savefig(fn_add_subfix(datafile,outSubfix,'.png'))

    