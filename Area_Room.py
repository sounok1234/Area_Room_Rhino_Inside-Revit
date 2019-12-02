"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "sounok.sarkar"
__version__ = "2019.10.21"

import clr
clr.AddReference('System.Core')
clr.AddReference('RhinoInside.Revit')
clr.AddReference('RevitAPI') 
clr.AddReference('RevitAPIUI')

from System.Linq import Enumerable
from Autodesk.Revit.DB import *
import Rhino as rh
from RhinoInside.Revit import Revit, Convert
import ghpythonlib as gh
import scriptcontext as sc
import rhinoscriptsyntax as rs

# Select polylines from rhino 
obj = rs.GetObjects("Please select multiple polyline curves", 0, True, True)
bool2 = rs.GetInteger("Press 0 to generate areas and 1 to generate rooms")
input_curves = []
for o in obj:
    input_curves.append(rs.coercecurve(o))

doc = Revit.ActiveDBDocument
tol = sc.doc.ModelAbsoluteTolerance
_t = 100000000

# Filter out various revit elements
levels = FilteredElementCollector(doc).OfClass(Level)
rooms = FilteredElementCollector(doc).OfClass(SpatialElement).OfCategory(BuiltInCategory.OST_Rooms).ToElements() 
areas = FilteredElementCollector(doc).OfClass(SpatialElement).OfCategory(BuiltInCategory.OST_Areas).ToElements() 
views = FilteredElementCollector(doc).OfClass(ViewPlan).ToElements() 
walls = FilteredElementCollector(doc).OfClass(Wall)
areaLines = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_AreaSchemeLines).ToElements()

# Get the view that supports area creation in Revit
true_views = []
for v in views:
    if v.ViewType == ViewType.AreaPlan:
        true_views.append(v)
    else:
        pass

# Individual edges from polylines in rhino
edges = []
surfaces = gh.components.BoundarySurfaces(input_curves)
for s in surfaces:
    edges.append(gh.components.DeconstructBrep(s)[1])

# Location of areas/rooms in UV format
pts = []
for t in input_curves:
    pt = rh.Geometry.AreaMassProperties.Compute(t).Centroid
    pts.append((int(pt.X), int(pt.Y)))
    for l in levels:
        if pt.Z == l.Elevation:
            level = l
        else:
            pass

def flatten(l): return flatten(l[0]) + (flatten(l[1:]) if len(l) > 1 else []) if type(l) is list else [l]

def GetLocation(lst):
    loc = []
    for l in lst:
        if l.Location == None:
            pass
        else:
            loc.append((int(l.Location.Point.X) , int(l.Location.Point.Y))) 
    return loc

def GetLocWalls(lst):
    new = []
    for l in lst:
        p = l.Location.Curve.Evaluate(0.5, True)
        new.append((int(p.X), int(p.Y)))
    return new

def cullDuplicateCurves(curves, _t, _tol):
    if len(curves) > 1:
        nc_objs = [crv.ToNurbsCurve() for crv in curves] 
        indx = []
        for i in range(len(nc_objs)):
            for k in range(len(nc_objs)):
                if (i != k) and (i not in indx) and (k not in indx) and (round(nc_objs[i].GetLength(), 3) == round(nc_objs[k].GetLength(), 3)):
                    if nc_objs[i].EpsilonEquals(nc_objs[k], _t):
                        crv1TVst = nc_objs[i].TangentAt(nc_objs[i].Domain[0])
                        crv1CVst = nc_objs[i].CurvatureAt(nc_objs[i].Domain[0])
                        crv1t1 = round( nc_objs[i].NormalizedLengthParameter( 0.33, rh.Geometry.Interval(0, nc_objs[i].GetLength()) )[1], 3 )
                        crv1CVmid1 = nc_objs[i].CurvatureAt(crv1t1)
                        crv1t2 = round( nc_objs[i].NormalizedLengthParameter( 0.66, rh.Geometry.Interval(0, nc_objs[i].GetLength()) )[1], 3 )
                        crv1CVmid2 = nc_objs[i].CurvatureAt(crv1t2)
                        crv1CVend = nc_objs[i].CurvatureAt(nc_objs[i].Domain[1])
                        crv1TVend = nc_objs[i].TangentAt(nc_objs[i].Domain[1])
                        crv2TVst = nc_objs[k].TangentAt(nc_objs[k].Domain[0])
                        crv2CVst = nc_objs[k].CurvatureAt(nc_objs[k].Domain[0])
                        crv2t1 = round( nc_objs[k].NormalizedLengthParameter( 0.33, rh.Geometry.Interval(0, nc_objs[k].GetLength()) )[1], 3 )
                        crv2CVmid1 = nc_objs[i].CurvatureAt(crv2t1)
                        crv2t2 = round( nc_objs[k].NormalizedLengthParameter( 0.66, rh.Geometry.Interval(0, nc_objs[k].GetLength()) )[1], 3 )
                        crv2CVmid2 = nc_objs[i].CurvatureAt(crv2t2)
                        crv2CVend = nc_objs[k].CurvatureAt(nc_objs[k].Domain[1])
                        crv2TVend = nc_objs[k].TangentAt(nc_objs[k].Domain[1])

                        crv2TVstR = rh.Geometry.Vector3d(crv2TVst)
                        crv2TVstR.Reverse()
                        crv2TVendR = rh.Geometry.Vector3d(crv2TVend)
                        crv2TVendR.Reverse()
                        crv2R = nc_objs[k].Duplicate()
                        crv2R.Reverse()
                        crv2TVstRR = crv2R.TangentAt(crv2R.Domain[0])
                        crv2CVstR = crv2R.CurvatureAt(crv2R.Domain[0])
                        crv2t1R = round( crv2R.NormalizedLengthParameter( 0.33, rh.Geometry.Interval(0, crv2R.GetLength()) )[1], 3 )
                        crv2CVmid1R = crv2R.CurvatureAt(crv2t1R)
                        crv2t2R = round( crv2R.NormalizedLengthParameter( 0.66, rh.Geometry.Interval(0, crv2R.GetLength()) )[1], 3 )
                        crv2CVmid2R = crv2R.CurvatureAt(crv2t2R)
                        crv2CVendR = crv2R.CurvatureAt(crv2R.Domain[1])
                        crv2TVendRR = crv2R.TangentAt(crv2R.Domain[1])
                        t1 = (nc_objs[i].Domain[0]+nc_objs[i].Domain[1])/2
                        midCrv1 = nc_objs[i].PointAt(t1)
                        t2 = (nc_objs[k].Domain[0]+nc_objs[k].Domain[1])/2
                        midCrv2 = nc_objs[k].PointAt(t2)
                        if ( midCrv1.EpsilonEquals(midCrv2, _tol) and crv1TVst.EpsilonEquals(crv2TVst, _tol) and crv1CVst.EpsilonEquals(crv2CVst, _t) and crv1CVmid1.EpsilonEquals(crv2CVmid1, _tol) and crv1CVmid2.EpsilonEquals(crv2CVmid2, _tol) and crv1CVend.EpsilonEquals(crv2CVend, _tol) and crv1TVend.EpsilonEquals(crv2TVend, _tol) )\
                        or ( midCrv1.EpsilonEquals(midCrv2, _tol) and crv1TVst.EpsilonEquals(crv2TVendR, _tol) and crv1CVst.EpsilonEquals(crv2CVend, _tol) and crv1CVmid1.EpsilonEquals(crv2CVmid2, _tol) and crv1CVmid2.EpsilonEquals(crv2CVmid1, _tol) and crv1CVend.EpsilonEquals(crv2CVst, _tol) and crv1TVend.EpsilonEquals(crv2TVstR, _tol) )\
                        or ( midCrv1.EpsilonEquals(midCrv2, _tol) and crv1TVst.EpsilonEquals(crv2TVstRR, _tol) and crv1CVst.EpsilonEquals(crv2CVstR, _tol) and crv1CVmid1.EpsilonEquals(crv2CVmid1R, _tol) and crv1CVmid2.EpsilonEquals(crv2CVmid2R, _tol) and crv1CVend.EpsilonEquals(crv2CVendR, _tol) and crv1TVend.EpsilonEquals(crv2TVendRR, _tol) ):
                            indx.append(i)

        for i in sorted(indx, reverse = True):  
            del curves[i] 
        return curves

new_edges = flatten(edges)
wall_curves = cullDuplicateCurves(new_edges, _t, tol)

def makeRoom():
    loc = GetLocation(rooms)
    with Transaction(doc, "makeRoom") as trans:
        trans.Start()
        for p in pts:
            if p in loc:
                pass
            else:
                doc.Create.NewRoom(level, UV(p[0], p[1]))
        trans.Commit()

def makeArea():
    loc = GetLocation(areas)
    with Transaction(doc, "makeArea") as trans:
        trans.Start()
        for p in pts:
            if p in loc:
                pass
            else:
                doc.Create.NewArea(true_views[0], UV(p[0], p[1]))
        trans.Commit()

def createWalls(curves):
    loc = GetLocWalls(walls)
    with Transaction(doc, "makeWall") as trans:
        trans.Start()
        for c in curves:
            pt = (int(c.PointAt(c.GetLength()/2).X), int(c.PointAt(c.GetLength()/2).Y)) 
            if pt in loc:
                pass
            else:
                p1 = c.PointAtStart
                p2 = c.PointAtEnd
                RevitCurve = Line.CreateBound(XYZ(p1.X, p1.Y, p1.Z), XYZ(p2.X, p2.Y, p2.Z))
                Wall.Create(doc, RevitCurve, level.Id, False)
        trans.Commit()

def createBoundary(curves):
    loc = GetLocWalls(areaLines)
    plane = Plane.CreateByNormalAndOrigin(XYZ(0,0,1), XYZ(0,0,0))
    with Transaction(doc, "makeBoundary") as trans:
        trans.Start()
        sktch = SketchPlane.Create(doc, plane)
        for c in curves:
            pt = (int(c.PointAt(c.GetLength()/2).X), int(c.PointAt(c.GetLength()/2).Y)) 
            if pt in loc:
                pass
            else:
                p1 = c.PointAtStart
                p2 = c.PointAtEnd
                RevitCurve = Line.CreateBound(XYZ(p1.X, p1.Y, p1.Z), XYZ(p2.X, p2.Y, p2.Z))
                doc.Create.NewAreaBoundaryLine(sktch, RevitCurve, true_views[0])
        trans.Commit()

def createSpaces(bool):
    if bool2 == 0:
        createBoundary(wall_curves)
        makeArea()
    else:
        createWalls(wall_curves)
        makeRoom()

createSpaces(bool)

