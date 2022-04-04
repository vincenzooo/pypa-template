

"""functions operating on a list of Data2D objects"""
# turned into a class derived from list 2020/01/16, no changes to interface,
# everything should work with no changes.

import os
import matplotlib.pyplot as plt
import numpy as np
import pdb

from pySurf.readers.format_reader import auto_reader
from pySurf.data2D import plot_data,get_data, level_data, save_data, rotate_data, remove_nan_frame, resample_data
from pySurf.data2D import read_data,sum_data, subtract_data, projection, crop_data, transpose_data, apply_transform, register_data
from plotting.multiplots import find_grid_size, subplot_grid
from pySurf.psd2d import psd2d,plot_psd2d,psd2d_analysis,plot_rms_power,rms_power
from plotting.backends import maximize
from plotting.add_clickable_markers import add_clickable_markers2

from pySurf.points import matrix_to_points2
from copy import deepcopy
from dataIO.span import span
from dataIO.fn_add_subfix import fn_add_subfix
from pySurf.data2D import projection
from pySurf.data2D_class import Data2D
from pySurf.data2D import levellegendre
from pySurf.affine2D import find_rototrans,find_affine
from pySurf.readers.instrumentReader import fitsWFS_reader

from IPython.display import display
from dataIO.superlist import Superlist
import itertools
from plotting.multiplots import commonscale

## FUNCTIONS ##

# Functions operating on a dlist as Python list of Data2D objects.
# Can be used equally on a Dlist object.

    
def topoints(data,level=None):
    """convert a dlist to single set of points containing all data.
    if level is passed, points are leveled and the value is passed as argument (e.g. level=(2,2) levels sag along two axis)."""
    if level is not None:
        plist = [d.level(level) for d in data] 
    plist = [d.topoints() for d in data]    
    return np.vstack(plist)

def load_dlist(rfiles,reader=None,*args,**kwargs):
    """Extracted from plot_repeat. Read a set of rfiles to a dlist.
    readers and additional arguments can be passed as scalars or lists.

    You can pass additional arguments to the reader in different ways:
     - pass them individually, they will be used for all readers
         load_dlist(.. ,option1='a',option2=1000)
     - to have individual reader parameters pass them as dictionaries (a same number as rfiles),
         load_dlist(.. ,{option1='a',option2=1000},{option1='b',option3='c'},..)
         in this case reader must be explicitly passed (None is acceptable value for auto).

    Example:
        dlist=load_dlist(rfiles,reader=fitsWFS_reader,scale=(-1,-1,1),
                units=['mm','mm','um'])

        dlist2=load_dlist(rfiles,fitsWFS_reader,[{'scale':(-1,-1,1),
                'units':['mm','mm','um']},{'scale':(1,1,-1),
                'units':['mm','mm','um']},{'scale':(-1,-1,1),
                'units':['mm','mm','$\mu$m']}])
    2019/04/08 made function general from plot_repeat, moved to dlist.
    """

    #pdb.set_trace()
    if reader is None:
        #reader=auto_reader(rfiles[0])
        reader = [auto_reader(r) for r in rfiles]
        
    if np.size(reader) ==1:
        reader=[reader]*len(rfiles)
        
    '''
    if kwargs : #passed explicit parameters for all readers
        pdb.set_trace()
        kwargs=[kwargs]*len(rfiles)
    else:
        if np.size(args) ==1:
            kwargs=[args]*len(rfiles)
        else:
            if np.size(args) != len(rfiles):
                raise ValueError
    '''

    if kwargs : #passed explicit parameters for each reader
        # Note, there is ambiguity when rfiles and a kwargs value have same
        # number of elements()
        #pdb.set_trace()
        #vectorize all values
        for k,v in kwargs.items():
            if (np.size(v) == 1):
                kwargs[k]=[v]*len(rfiles)    
            elif (len(v) != len(rfiles)):
                kwargs[k]=[v]*len(rfiles)
            #else:  #non funziona perche' ovviamente anche chiamando esplicitamente, sara'
            #  sempre di lunghezza identica a rfiles.
            #    print ('WARNING: ambiguity detected, it is not possible to determine'+
            #    'if `%s` values are intended as n-element value or n values for each data.\n'+
            #    'To solve, call the function explicitly repeating the value.'%k)
    
    # 2020/07/10 args overwrite kwargs (try to avoid duplicates anyway).
    # args were ignored before.
    
    if not args:  #assume is correct number of elements
        args = [[]]*len(rfiles)
    
    #pdb.set_trace()
    
    #transform vectorized kwargs in list of kwargs
    kwargs=[{k:v[i] for k,v in kwargs.items()} for i in np.arange(len(rfiles))]
    
    #kwargs here is a list of dictionaries {option:value}, matching the readers
    #dlist=[Data2D(file=wf1,reader=r,**{**k, **a}) for wf1,r,k,a in zip(rfiles,reader,args,kwargs)]
    dlist=[Data2D(file=wf1,reader=r,*a,**k) for wf1,r,a,k in zip(rfiles,reader,args,kwargs)]
    
    return dlist

def test_load_dlist(rfiles):

    dlist=load_dlist(rfiles,reader=fitsWFS_reader,scale=(-1,-1,1),
            units=['mm','mm','um'])

    dlist2=load_dlist(rfiles,fitsWFS_reader,[{'scale':(-1,-1,1),
            'units':['mm','mm','um']},{'scale':(1,1,-1),
            'units':['mm','mm','um']},{'scale':(-1,-1,1),
            'units':['mm','mm','$\mu$m']}])
    return dlist,dlist2

def plot_data_repeat(dlist,name="",num=None,*args,**kwargs):
    """"given a list of Data2D objects dlist, plots them as subplots on a grid with shared x and y scales in maximized window. colorscale is independent for each subplot.
    returns stats.
    num is the figure number to plot on a specofic figure, other arguments are passed to plot.
    """

    res=[]
    #fig,axes=plt.subplots(1,len(dlist),num=1)
    xs,ys=find_grid_size(len(dlist),3,square=False)
    fig,axes=plt.subplots(xs,ys,num=num,clear=True)
    plt.close() #prevent from showing inline in notebook with %matplotlib inline
    axes=axes.flatten()
    maximize()
    
    for i,(ll,ax) in enumerate(zip(dlist,axes)):
        plt.subplot(xs,ys,i+1,sharex=axes[0],sharey=axes[0])
        ll.plot(stats=True,*args,**kwargs)
        res.append(ll.std())
        #plt.clim([-3,3])
        plt.clim(*(np.nanmean(ll.data)+np.nanstd(ll.data)*np.array([-1,1])))
    plt.suptitle(name+' RAW (plane level)')
    for ax in axes[:len(dlist)-1:-1]:
        fig.delaxes(ax)
        #plt.pause(0.1)
        
    commonscale(plt.gcf())
        
    return res       

def dcouples_plot(dlist,level=True):
    """calculate and plots rotating differences, data are supposed to be already aligned. 
    plots are generated on a grid, x and y axes are shared, color scale is automatic for each subplot.
    Note, data are leveled by default (level=True).
    
    """
    
    dcouples=[c[1]-c[0] for c in list(itertools.combinations(dlist, 2))]
    if level:
        dcouples=[d.level() for d in dcouples]

    plt.clf()
    maximize()
    
    xs,ys=find_grid_size(len(dcouples),square=True)[::-1]
    fig,axes=plt.subplots(xs,ys)
    plt.close() #prevent from showing inline in notebook with %matplotlib inline
    if len(np.shape(axes))>1:
        axes=axes.flatten()
    elif len(np.shape(axes))==0:
        axes=[axes]
    maximize()
    for i,(ll,ax) in enumerate(zip(dcouples,axes)):
        plt.subplot(xs,ys,i+1,sharex=axes[0],sharey=axes[0])
        ll.plot()
        plt.clim(*(ll.std()*np.array([-1,1])))
    for ax in axes[:len(dcouples)-1:-1]:
        fig.delaxes(ax)
        #plt.pause(0.1)
    #plt.tight_layout()
    

    #return [d.std() for d in [diff21,diff31,diff32]]
    return dcouples


def compare_images(datalist, x=None, y=None, fignum=None, titles=None,
                   vmin=None, vmax=None, commonscale=False, axis=0, axmax=0,
                   *args, **kwargs):
    """return a generator that plots n images in a list in subplots with shared
    zoom and axes. datalist is a list of data in format (data, x, y).
    x and y provide plot range (temporarily, ideally want to be able to 
    plot same scale).
    fignum window where to plot, if fignnum is 0 current figure is cleared,
    if None new figure is created.
    axis defines the axis with larger number of plots (default ncols >= nrows)
    axmax maximum nr of plots along shorter dim.
    """
    #modified again 2018/06/05 to accept list of data,x,y triplets. x and y are 
    # accepted as range.
    # old docstring was:
    # return a generator that plots n images in a list in subplots with shared
    # zoom and axes. datalist is a list of 2d data on same x and y.
    # fignum window where to plot, if fignnum is 0 current figure is cleared,
    # if None new figure is created.
    
    
    # this was changed a couple of times in interface, for example in passing
    # ((data,x,y),...) rather than (data1,data2),x,y
    # it can be tricky in a general way if data don't have all same size,
    # at the moment it is assumed they have.
    # in any case x and y are used only to generate the extent,
    # that is then adapted to the size of data.

    gridsize = find_grid_size(len(datalist),axmax)
    if axis == 1: gridsize=gridsize[::-1]

    fig = fignumber(fignum)

    plt.clf()
    ax = None

    # this is to set scale if not fixed
    d1std = [np.nanstd(data[0]) for data in datalist]
    std = min(d1std)

    for i, d in enumerate(datalist):
        """adjust to possible input formats"""
        data, x, y = d
        if x is None:
            x = np.arange(data.shape[1])
        if y is None:
            y = np.arange(data.shape[0])
        ax = plt.subplot(gridsize[0], gridsize[1], i+1, sharex=ax, sharey=ax)
        if titles is not None:
            print("titles is not none, it is ", titles)
            plt.title(titles[i])
        # plt.xlabel('X (mm)')
        # plt.ylabel('Y (mm)')
        s = (std if commonscale else d1std[i])
        d1mean = np.nanmean(data)
        aspect=kwargs.pop('aspect',None)
        axim = plt.imshow(data, extent=np.hstack([span(x),span(y)]),
                          interpolation='none', aspect=aspect,
                          vmin=kwargs.get('vmin', d1mean-s),
                          vmax=kwargs.get('vmax', d1mean+s),
                          *args, **kwargs)
        plt.colorbar()
        yield ax

def multimarkers(datalist):
    """add clickable markers to a list of data using `add_clickable_markers2`. 
    Not sure it is updated, see also Dlist."""
    
    
    plt.figure()
    
    #difficile condividere gli assi visto che non possono essere passati
    s=subplot_grid(len(datalist))
    a=[add_clickable_markers2(s[0])]
    for ss in s[1:-1]:
        plot_data(datalist)
        a.append(add_clickable_markers2(ss))
    a.append(add_clickable_markers2(s[-1],hold=True))
    return a

def mark_data(datalist,outfile=None,deg=1,levelfunc=None,propertyname='markers',direction=0):
    """plot all data in a set of subplots. Allows to interactively put markers
    on each of them. Return list of axis with attached property 'markers'"""
    import logging
    from matplotlib.widgets import MultiCursor
    from plotting.add_clickable_markers import add_clickable_markers2

    try:
        logger
    except NameError:
        logger=logging.getLogger()
        logger.setLevel(logging.DEBUG)
    #datalist = [d() for d in datalist]]
    axes=list(compare_images([[levellegendre(y,wdata,deg=6),x,y] for (wdata,x,y) in datalist],
        commonscale=True,direction=direction))
    fig=plt.gcf()
    multi = MultiCursor(fig.canvas, axes, color='r', lw=.5, horizOn=True, vertOn=True)
    plt.title('6 legendre removed')

    if outfile is not None:
        if os.path.exists(fn_add_subfix(outfile,'_markers','.dat')):
            np.genfromtxt(fn_add_subfix(outfile,'_markers','.dat'))

    for a in axes:
        a.images[0].set_clim(-0.01,0.01)
        add_clickable_markers2(ax=a,propertyname=propertyname) #,block=True)

    #display(plt.gcf())

    #Open interface. if there is a markers file, read it and plot markers.
    #when finished store markers

    for a in axes:
        logger.info('axis: '+str(a))
        logger.info('markers: '+str(a.markers))
        print(a.markers)

    if outfile is not None:
        np.savetxt(fn_add_subfix(outfile,'_markers','.dat'),np.array([a.markers for a in axes]))
        plt.savefig(fn_add_subfix(outfile,'_markers','.png'))

    return axes

def add_markers(dlist):
    """interactively set markers, when ENTER is pressed,
    return markers as list of ndarray.
    It was align_active interactive, returning also trans, this returns only markers,
    transforms can be obtained by e.g. :
    m_trans=find_transform(m,mref) for m in m_arr]
      """

    #set_alignment_markers(tmp)
    xs,ys=find_grid_size(len(dlist),5)[::-1]

    # differently from plt.subplots, axes are returned as list,
    # beacause unused axes were removed (in future if convenient it could
    # make return None for empty axes)
    fig,axes=subplot_grid(len(dlist),(xs,ys),sharex='all',sharey='all')

    #axes=axes.flatten()  #not needed because a list
    maximize()
    for i,(d,ax) in enumerate(zip(dlist,axes)):
        plt.sca(ax)
        #ll=d.level(4,byline=True)
        ll = d
        ll.plot()
        #plt.clim(*remove_outliers(ll.data,nsigma=2,itmax=1,span=True))
        add_clickable_markers2(ax,hold=(i==(len(dlist)-1)))

    return [np.array(ax.markers) for ax in axes]

def align_interactive(dlist,find_transform=find_affine,mref=None):
    """plot a list of Data2D objects on common axis and allow to set
    markers. When ENTER is pressed, return markers and transformations"""

    m_arr = add_markers (dlist)

    #populate array of transforms
    mref = mref if mref is not None else m_arr[0]
    m_trans = [find_transform(m,mref) for m in m_arr]

    return m_arr,m_trans

def psd2an(dlist,wfun=np.hanning,
                ymax=None,outfolder="",subfix='_psd2d',*args,**kwargs):
    """2d psd analysis with threshold on sag removed data. Return a list of psd2d.
    ymax sets top of scale for rms right axis.
    if outfolder is provided, save psd2d_analysis plot with dlist names+subfix"""
    m_psd=[]
    title = kwargs.pop('title','')
    #pdb.set_trace()
    for dd in dlist:
        m_psd.append(dd.level(2,axis=0).psd(analysis=True,
            title=title,wfun=wfun,*args,**kwargs))
        #psd2d_analysis(*dd.level(2,byline=True)(),
        #                 title=os.path.basename(outfolder),wfun=wfun,*args,**kwargs)
        #m_psd.append((fs,ps))
        ax=plt.gcf().axes[-1]
        ax.set_ylim([0,ymax])
        plt.grid(0)
        ax.grid()
        plt.suptitle(dd.name+' - hanning window - sag removed by line')
        if outfolder is not None:
            plt.savefig(os.path.join(outfolder,dd.name+subfix+'.png'))
        #pr=projection(pl[0].data,axis=1,span=1)
        #plot_psd(pl[0].y,pr[0],label='avg')
        #plot_psd(pl[0].y,pr[1],label='min')
        #plot_psd(pl[0].y,pr[2],label='max')
    return m_psd

def extract_psd(dlist,rmsthr=0.07,rmsrange=None,prange=None,ax2f=None,dis=False):
    """use psd2an, from surface files return linear psd."""
    m_psd=psd2an(dlist,rmsthr=rmsthr,rmsrange=rmsrange,prange=prange,ax2f=ax2f,dis=dis)

    plt.figure()
    plt.clf()
    labels=[d.name for d in dlist]
    m_tot=[]
    #gives error, m_psd is a list of PSD2D objects, there is no f,p, check psd2an
    for P,l in zip(m_psd,labels):
        (f,p) = P()
        ptot=projection(p,axis=1)
        #plot_psd(f,ptot,label=l,units=d.units)
        #np.savetxt(fn_add_subfix(P.name,'_calib_psd','.dat',
        #    pre=outfolder+os.path.sep),np.vstack([fs,ptot]).T,
        #    header='SpatialFrequency(%s^-1)\tPSD(%s^2 %s)'%(u[0],u[2],u[0]))
        m_tot.append((f,ptot))
    # plt.title(outname)

    plt.legend(loc=0)
    if dis:
        display(plt.gcf())
    return m_tot

def psd2d(dlist,ymax=None,subfix='_psd2d',*args,**kwargs):
    """2d psd analysis of a dlist. 
    Doesn't do any additional processing or plotting (must be done externally)
    [`outfolder` is being removed].
    Any parameter for `Data2D.psd` are accepted,
    however, parameters are not vectorized (must be the same for all data).
    [see example of vectorization e.g. in `load_dlist`] 
    Return a list of psd2d.
    
    from `psd2an`
    ymax sets top of scale for rms right axis.
    if outfolder is provided, save psd2d_analysis plot with dlist names+subfix"""
    
    m_psd=[]
    title = kwargs.pop('title','')
    #pdb.set_trace()
    for dd in dlist:
        m_psd.append(dd.psd(analysis=True,
            title=title,wfun=wfun,*args,**kwargs))
        #psd2d_analysis(*dd.level(2,byline=True)(),
        #                 title=os.path.basename(outfolder),wfun=wfun,*args,**kwargs)
        #m_psd.append((fs,ps))
        ax=plt.gcf().axes[-1]
        ax.set_ylim([0,ymax])
        plt.grid(0)
        ax.grid()
        plt.suptitle(dd.name+' - hanning window - sag removed by line')
        if outfolder is not None:
            plt.savefig(os.path.join(outfolder,dd.name+subfix+'.png'))
        #pr=projection(pl[0].data,axis=1,span=1)
        #plot_psd(pl[0].y,pr[0],label='avg')
        #plot_psd(pl[0].y,pr[1],label='min')
        #plot_psd(pl[0].y,pr[2],label='max')
    return m_psd

## CLASS ##

# Minimal implementation, should broadcast properties

class Dlist(Superlist):
    """A list of pySurf.Data2D objects on which unknown operations are performed serially."""           
    
    def topoints(self,level=True):
        """convert a dlist to single set of points containing all data."""
        plist = topoints(self.data,level = None)
        return plist  