### BEGIN LICENSE BLOCK
# I don't understand about licenses.
# Do what you want with it.
### END LICENSE BLOCK
bl_info = {'name':'Voronoi Linker','author':'ugorek','version':(1,6,4),'blender':(3,4,0), #28.12.2022
        'description':'Simplification of create node links.','location':'Node Editor > Alt + RBM','warning':'','category':'Node',
        'wiki_url':'https://github.com/ugorek000/VoronoiLinker/blob/main/README.md','tracker_url':'https://github.com/ugorek000/VoronoiLinker/issues'}
#This addon is a self-writing for me personally, which I made publicly available to everyone wishing. Enjoy it if you want to enjoy.

import bpy, bgl, blf, gpu; from gpu_extras.batch import batch_for_shader
from mathutils import Vector; from math import pi, sin, cos, tan, asin, acos, atan, atan2, sqrt, inf, copysign

def uiScale(): return bpy.context.preferences.system.dpi*bpy.context.preferences.system.pixel_size/72
def PosViewToReg(x,y): return bpy.context.region.view2d.view_to_region(x,y,clip=False)
shader = [None,None]; uiFac = [1.0]
def DrawWay(vtxs,vcol,siz):
    bgl.glEnable(bgl.GL_BLEND); bgl.glEnable(bgl.GL_LINE_SMOOTH); shader[0].bind()
    bgl.glLineWidth(siz); batch_for_shader(shader[0],'LINE_STRIP',{'pos':vtxs,'color':vcol}).draw(shader[0])
def DrawAreaFan(vtxs,col,sm):
    bgl.glEnable(bgl.GL_BLEND); bgl.glEnable(bgl.GL_POLYGON_SMOOTH) if sm else bgl.glDisable(bgl.GL_POLYGON_SMOOTH); shader[1].bind()
    shader[1].uniform_float('color',col); batch_for_shader(shader[1],'TRI_FAN',{'pos':vtxs}).draw(shader[1])
def DrawLine(ps1,ps2,sz=1,cl1=(1.0,1.0,1.0,0.75),cl2=(1.0,1.0,1.0,0.75),fs=[0,0]): DrawWay(((ps1[0]+fs[0],ps1[1]+fs[1]),(ps2[0]+fs[0],ps2[1]+fs[1])),(cl1,cl2),sz)
def DrawCircleOuter(pos,rd,siz=1,col=(1.0,1.0,1.0,0.75),resolution=16):
    vtxs = []; vcol = []
    for cyc in range(resolution+1): vtxs.append((rd*cos(cyc*2*pi/resolution)+pos[0],rd*sin(cyc*2*pi/resolution)+pos[1])); vcol.append(col)
    DrawWay(vtxs,vcol,siz)
def DrawCircle(pos,rd,col=(1.0,1.0,1.0,0.75),resl=54): DrawAreaFan([(pos[0],pos[1]),*[(rd*cos(i*2*pi/resl)+pos[0],rd*sin(i*2*pi/resl)+pos[1]) for i in range(resl+1)]],col,True)
def DrawWidePoint(pos,rd,colfac=Vector((1,1,1,1))):
    col1 = Vector((0.5,0.5,0.5,0.4)); col2 = Vector((0.5,0.5,0.5,0.4)); col3 = Vector((1,1,1,1))
    colfac = colfac if DrawPrefs().dsIsColoredPoint else Vector((1,1,1,1)); rd = sqrt(rd*rd+10); rs = DrawPrefs().dsPointResolution
    DrawCircle(pos,rd+3,col1*colfac,rs); DrawCircle(pos,rd,col2*colfac,rs); DrawCircle(pos,rd/1.5,col3*colfac,rs)
def DrawRectangle(ps1,ps2,cl): DrawAreaFan([(ps1[0],ps1[1]),(ps2[0],ps1[1]),(ps2[0],ps2[1]),(ps1[0],ps2[1])],cl,False)
def DrawRectangleOnSocket(context,sk,stEn,colfac=Vector((1,1,1,1))):
    if DrawPrefs().dsIsDrawArea==False: return
    loc = RecrGetNodeFinalLoc(sk.node).copy()*uiFac[0]; pos1 = PosViewToReg(loc.x,stEn[0]*uiFac[0]); colfac = colfac if DrawPrefs().dsIsColoredArea else Vector((1,1,1,1))
    pos2 = PosViewToReg(loc.x+sk.node.dimensions.x,stEn[1]*uiFac[0]); DrawRectangle(pos1,pos2,Vector((1.0,1.0,1.0,0.075))*colfac)
fontId = [0]; where = [None]; NowTool = [0]

def RecrGetNodeFinalLoc(node): return node.location if node.parent==None else node.location+RecrGetNodeFinalLoc(node.parent)
def GetNearestNodeInRegionMouse(context): #Ищет ближайший нод к курсору. Честное поле расстояний. Спасибо RayMarching'у, без него я бы до такого не допёр.
    goalNd = None; goalPs = None; minLen = inf
    def ToSign(vec2): return Vector((copysign(1,vec2[0]),copysign(1,vec2[1]))) #Для запоминания своего квадранта перед abs().
    mousePs = context.space_data.cursor_location; nodes = context.space_data.edit_tree.nodes
    for nd in nodes:
        #Игнорировать рамки. Игнорировать свёрнутые ноды. Триггериться на рероуты, которые могут быть свёрнутыми
        if (nd.bl_idname!='NodeFrame')and((nd.hide==False)or(nd.bl_idname=='NodeReroute')):
            #Для инструмента Предпросмотра игнорировать свой собственный спец-рероут-якорь (полное совпадение имени и заголовка);
            #Если Предпросмотр, то игнорировать ноды с пустыми выходами, чтобы точка не висела просто так и нод не мешал для удобного использования Предпросмотра
            if ((nd.name!='Voronoi_Anchor')or(nd.label!='Voronoi_Anchor')or(NowTool[0]!=3))and((NowTool[0]!=3)or(len(nd.outputs)!=0)):
                #Если Предпросмотр в геометрических нодах, триггериться только на ноды, содержащие выход геометрии
                if (NowTool[0]==3)and(context.space_data.tree_type=='GeometryNodeTree'):
                    if [ndo for ndo in nd.outputs if ndo.type=='GEOMETRY']==[]: continue
                #Расчехлить иерархию родителей и получить итоговую позицию нода. Подготовить размер нода
                locNd = RecrGetNodeFinalLoc(nd); sizNd = Vector((4,4)) if nd.bl_idname=='NodeReroute' else nd.dimensions/uiFac[0]
                #Для рероута позицию в центр, для нода позицию в нижний левый угол
                locNd = locNd-sizNd/2 if nd.bl_idname=='NodeReroute' else locNd-Vector((0,sizNd[1]))
                #Обожаю RayMarching:
                fieldUV = mousePs-(locNd+sizNd/2); fieldXY = Vector((abs(fieldUV.x),abs(fieldUV.y)))-sizNd/2
                fieldXY = Vector((max(fieldXY.x,0),max(fieldXY.y,0))); fieldL = fieldXY.length
                #Если выборка поля расстояний в позиции курсора меньше минимально запомненной, установить новую ближайшую. Позиция = курсор - восстановленное направление
                if fieldL<minLen: minLen = fieldL; goalNd = nd; goalPs = mousePs-fieldXY*ToSign(fieldUV)
    return goalNd, goalPs, minLen
SkPerms = ['VALUE','RGBA','VECTOR','INT','BOOLEAN']
def GetNearestSocketInRegionMouse(context,getOut,skOut): #Ищет ближайший сокет у ближайшего нода. Честное поле расстояний ячейками Вороного.
    #Этот поиск уже включает поиск ближайшего нода
    mousePs = context.space_data.cursor_location; nd = GetNearestNodeInRegionMouse(context)[0]
    #Если ближайший нод не найден, искать не у кого
    if nd==None: return None, None, inf, (0,0)
    #Так же расшифровать иерархию родителей, как и в поиске ближайшего нода, потому что теперь ищутся сокеты
    locNd = RecrGetNodeFinalLoc(nd)
    #Если рероут, то простой вариант не требующий вычисления; вход и выход всего одни, позиция сокета -- он сам
    if nd.bl_idname=='NodeReroute': return nd.outputs[0] if getOut else nd.inputs[0], nd.location, Vector(mousePs-nd.location).length, (-1,-1)
    #Подготовиться для поиска:
    goalSk = None; goalPs = None; minLen = inf; skHigLigHei = (0,0); ndDim = nd.dimensions/uiFac[0]
    #Установить "каретку" в первый сокет своей стороны. Верхний если выход, нижний если вход
    skLoc = Vector((locNd.x+ndDim[0],locNd.y-35)) if getOut else Vector((locNd.x,locNd.y-ndDim[1]+16))
    for wh in nd.outputs if getOut else reversed(nd.inputs):
        #Игнорировать выключенные и спрятанные
        if (wh.enabled)and(wh.hide==False):
            muv = 0; tgl = False # muv -- для высоты варпа от вектор-сокетов-не-в-одну-строчку. tgl -- чтобы разбить условия на несколько строчек (слешем не желаю).
            #Если текущий сокет -- входящий вектор, и он свободный и не спрятан в одну строчку
            if (getOut==False)and(wh.type=='VECTOR')and(wh.is_linked==False)and(wh.hide_value==False):
                #Ручками вычисляем занимаемую высоту сокета. Для сферы направления у ShaderNodeNormal и таких же у групп;
                #И для особо-отличившихся нод с векторами, которые могут быть в одну строчку
                if str(wh.bl_rna).find('VectorDirection')!=-1: skLoc[1] += 20*2; muv = 2
                elif ((nd.type in ('BSDF_PRINCIPLED','SUBSURFACE_SCATTERING'))==False)or((wh.name in ('Subsurface Radius','Radius'))==False): skLoc[1] += 30*2; muv = 3
            if skOut!=None: #Если есть контекст для поиска входа
                #Виртуальными -- любой к любому (диаметральные случаи).
                #Любой сокет для виртуального выхода; разрешить в виртуальный при получении входа для любого сокета. Побочный эффект - виртуальный в виртуальный
                tgl = (skOut.bl_idname=='NodeSocketVirtual')or((wh.bl_idname=='NodeSocketVirtual')and(not getOut))
                #Для разрешённой-группы-между-собой разрешить "переходы". Рероутом для удобства можно в любой сокет минуя разные типы.
                #Предыдущий результат + если выход и вход в разрешённых-между-собой; или у обоих одинаковые типы; или выходом является рероут
                tgl = (tgl)or((skOut.type in SkPerms)and(wh.type in SkPerms))or(skOut.bl_idname==wh.bl_idname)or(skOut.node.type=='REROUTE')
            if NowTool[0]==2: tgl = (getOut)and(skOut==None)or(tgl) #Головная боль.
            else: tgl = (getOut)or(skOut==None)or(tgl) # "or(skOut==None)" -- если требуется просто найти вход без контекста выхода
            #Для превиева игнорировать виртуальные. 
            if (tgl)and((NowTool[0]!=3)or(wh.bl_idname!='NodeSocketVirtual')):
                #Расстояние от курсора до ручками подсчитанной позиции сокета. Если меньше запомненной -- новый ближайший сокет
                fieldXY = mousePs-skLoc; fieldL = fieldXY.length
                # skHigLigHei так же учитывает текущую высоту мульти-инпута
                if fieldL<minLen: minLen = fieldL; goalSk = wh; goalPs = skLoc.copy(); skHigLigHei = (goalPs[1]-11-muv*20,goalPs[1]+11+max(len(wh.links)-2,0)*5)
            #Сдвинуть до следующего на своё направление
            skLoc[1] += 22*(1-getOut*2)
    return goalSk, goalPs, minLen, skHigLigHei
def GetSkCol(Sk): return Sk.draw_color(bpy.context,Sk.node)
def Vec4Pow(vec,pw): return Vector((vec.x**pw,vec.y**pw,vec.z**pw,vec.w**pw))
def GetSkVecCol(Sk,apw): return Vec4Pow(Vector(Sk.draw_color(bpy.context,Sk.node)),1/apw)

def DrawPrefs(): return bpy.context.preferences.addons[__name__ if __name__!='__main__' else 'VoronoiLinker'].preferences
def SetFont(): fontId[0] = blf.load(r'C:\Windows\Fonts\consola.ttf'); fontId[0] = 0 if fontId[0]==-1 else fontId[0] #for change Blender themes

def DrawSkText(pos,ofsx,ofsy,Sk):
    if DrawPrefs().dsIsDrawSkText==False: return 0
    try: skCol = GetSkCol(Sk)
    except: skCol = (1,0,0,1)
    skCol = skCol if DrawPrefs().dsIsColoredText else (.9,.9,.9,1); txt = Sk.name if Sk.bl_idname!='NodeSocketVirtual' else 'Virtual'
    isdrsh = DrawPrefs().dsIsDrawSkTextShadow
    if isdrsh:
        blf.enable(fontId[0],blf.SHADOW); sdcol = DrawPrefs().dsShadowCol; blf.shadow(fontId[0],[0,3,5][DrawPrefs().dsShadowBlur],sdcol[0],sdcol[1],sdcol[2],sdcol[3])
        sdofs = DrawPrefs().dsShadowOffset; blf.shadow_offset(fontId[0],sdofs[0],sdofs[1])
    else: blf.disable(fontId[0],blf.SHADOW)
    tof = DrawPrefs().dsTextFrameOffset; txsz = DrawPrefs().dsFontSize; blf.size(fontId[0],txsz,72)
    txdim = [blf.dimensions(fontId[0],txt)[0],blf.dimensions(fontId[0],'█')[1]]
    pos = [pos[0]-(txdim[0]+tof+10)*(ofsx<0)+(tof+1)*(ofsx>-1),pos[1]+tof]; pw = 1/1.975
    muv = round((txdim[1]+tof*2)*ofsy)
    pos1 = [pos[0]+ofsx-tof,pos[1]+muv-tof]; pos2 = [pos[0]+ofsx+10+txdim[0]+tof,pos[1]+muv+txdim[1]+tof]
    list = [.4,.55,.7,.85,1]; uh = 1/len(list)*(txdim[1]+tof*2)
    if DrawPrefs().dsTextStyle=='Classic':
        for cyc in range(len(list)): DrawRectangle([pos1[0],pos1[1]+cyc*uh],[pos2[0],pos1[1]+cyc*uh+uh],(skCol[0]/2,skCol[1]/2,skCol[2]/2,list[cyc]))
        col = (skCol[0]**pw,skCol[1]**pw,skCol[2]**pw,1)
        DrawLine(pos1,[pos2[0],pos1[1]],1,col,col); DrawLine([pos2[0],pos1[1]],pos2,1,col,col)
        DrawLine(pos2,[pos1[0],pos2[1]],1,col,col); DrawLine([pos1[0],pos2[1]],pos1,1,col,col)
        col = (col[0],col[1],col[2],.375); thS = DrawPrefs().dsTextLineframeOffset
        DrawLine(pos1,[pos2[0],pos1[1]],1,col,col,[0,-thS]); DrawLine([pos2[0],pos1[1]],pos2,1,col,col,[+thS,0])
        DrawLine(pos2,[pos1[0],pos2[1]],1,col,col,[0,+thS]); DrawLine([pos1[0],pos2[1]],pos1,1,col,col,[-thS,0])
        DrawLine([pos1[0]-thS,pos1[1]],[pos1[0],pos1[1]-thS],1,col,col); DrawLine([pos2[0]+thS,pos1[1]],[pos2[0],pos1[1]-thS],1,col,col)
        DrawLine([pos2[0]+thS,pos2[1]],[pos2[0],pos2[1]+thS],1,col,col); DrawLine([pos1[0]-thS,pos2[1]],[pos1[0],pos2[1]+thS],1,col,col)
    elif DrawPrefs().dsTextStyle=='Simplified':
        DrawRectangle([pos1[0],pos1[1]],[pos2[0],pos2[1]],(skCol[0]/2.4,skCol[1]/2.4,skCol[2]/2.4,.8)); col = (.1,.1,.1,.95)
        DrawLine(pos1,[pos2[0],pos1[1]],2,col,col); DrawLine([pos2[0],pos1[1]],pos2,2,col,col)
        DrawLine(pos2,[pos1[0],pos2[1]],2,col,col); DrawLine([pos1[0],pos2[1]],pos1,2,col,col)
    blf.position(fontId[0],pos[0]+ofsx+3.5,pos[1]+muv+txdim[1]*.3,0); blf.color(fontId[0],skCol[0]**pw,skCol[1]**pw,skCol[2]**pw,1.0); blf.draw(fontId[0],txt)
    return [txdim[0]+tof,txdim[1]+tof*2]
def DrawIsLinked(loc,ofsx,ofsy,skCol):
    ofsx += ((20+DrawPrefs().dsTextDistFromCursor)*1.5+DrawPrefs().dsTextFrameOffset)*copysign(1,ofsx)+4
    if DrawPrefs().dsIsDrawMarker==False: return
    vec = PosViewToReg(loc.x,loc.y); gc = 0.65; col1 = (0,0,0,0.5); col2 = (gc,gc,gc,max(max(skCol[0],skCol[1]),skCol[2])*.9); col3 = (skCol[0],skCol[1],skCol[2],.925)
    DrawCircleOuter([vec[0]+ofsx+1.5,vec[1]+3.5+ofsy],9.0,3.0,col1); DrawCircleOuter([vec[0]+ofsx-3.5,vec[1]-5+ofsy],9.0,3.0,col1)
    DrawCircleOuter([vec[0]+ofsx,vec[1]+5+ofsy],9.0,3.0,col2); DrawCircleOuter([vec[0]+ofsx-5,vec[1]-3.5+ofsy],9.0,3.0,col2)
    DrawCircleOuter([vec[0]+ofsx,vec[1]+5+ofsy],9.0,1.0,col3); DrawCircleOuter([vec[0]+ofsx-5,vec[1]-3.5+ofsy],9.0,1.0,col3)

def PreparGetWP(loc,offsetx): pos = PosViewToReg(loc.x+offsetx,loc.y); rd = PosViewToReg(loc.x+offsetx+6*DrawPrefs().dsPointRadius,loc.y)[0]-pos[0]; return pos,rd
def DebugDrawCallback(sender,context):
    def DrawText(pos,txt,r=1,g=1,b=1): blf.size(fontId[0],14,72); blf.position(fontId[0],pos[0]+10,pos[1],0); blf.color(fontId[0],r,g,b,1.0); blf.draw(fontId[0],txt)
    mousePos = context.space_data.cursor_location*uiFac[0]
    wp = PreparGetWP(mousePos,0); DrawWidePoint(wp[0],wp[1]); DrawText(PosViewToReg(mousePos[0],mousePos[1]),'Cursor pos here!')
    wp = PreparGetWP(GetNearestNodeInRegionMouse(context)[1],0); DrawWidePoint(wp[0],wp[1],Vector((1,.5,.5,1))); DrawText(wp[0],'Nearest node here!',g=.5,b=.5)
    muc = GetNearestSocketInRegionMouse(context,True,None)[1]
    if muc!=None: wp = PreparGetWP(muc,0); DrawWidePoint(wp[0],wp[1],Vector((.5,1,.5,1))); DrawText(wp[0],'Nearest socketOut here!',r=.5,b=.5)
    muc = GetNearestSocketInRegionMouse(context,False,None)[1]
    if muc!=None: wp = PreparGetWP(muc,0); DrawWidePoint(wp[0],wp[1],Vector((.5,.5,1,1))); DrawText(wp[0],'Nearest socketIn here!',r=.75,g=.75)
    
def VoronoiLinkerDrawCallback(sender,context):
    if where[0]!=context.space_data: return
    shader[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR'); shader[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR'); bgl.glHint(bgl.GL_LINE_SMOOTH_HINT,bgl.GL_NICEST)
    if DrawPrefs().dsIsDrawDebug: DebugDrawCallback(sender,context); return
    mousePos = context.space_data.cursor_location*uiFac[0]; lw = DrawPrefs().dsLineWidth
    def MucDrawSk(Sk,lh):
        txtdim = DrawSkText(PosViewToReg(mousePos.x,mousePos.y),-DrawPrefs().dsTextDistFromCursor*(Sk.is_output*2-1),-.5,Sk)
        if Sk.is_linked: DrawIsLinked(mousePos,-txtdim[0]*(Sk.is_output*2-1),0,GetSkCol(Sk) if DrawPrefs().dsIsColoredMarker else (.9,.9,.9,1))
    if (sender.sockOutSk==None):
        if DrawPrefs().dsIsDrawPoint:
            wp1 = PreparGetWP(mousePos,-DrawPrefs().dsPointOffsetX*.75); wp2 = PreparGetWP(mousePos,DrawPrefs().dsPointOffsetX*.75)
            DrawWidePoint(wp1[0],wp1[1]); DrawWidePoint(wp2[0],wp2[1])
        if (DrawPrefs().dsIsAlwaysLine)and(DrawPrefs().dsIsDrawLine): DrawLine(wp1[0],wp2[0],lw,(1,1,1,1),(1,1,1,1))
    elif (sender.sockOutSk!=None)and(sender.sockInSk==None):
        DrawRectangleOnSocket(context,sender.sockOutSk,sender.sockOutLH,GetSkVecCol(sender.sockOutSk,2.2))
        wp1 = PreparGetWP(sender.sockOutPs*uiFac[0],DrawPrefs().dsPointOffsetX); wp2 = PreparGetWP(mousePos,0)
        if (DrawPrefs().dsIsAlwaysLine)and(DrawPrefs().dsIsDrawLine): DrawLine(wp1[0],wp2[0],lw,GetSkCol(sender.sockOutSk) if DrawPrefs().dsIsColoredLine else (1,1,1,1),(1,1,1,1))
        if DrawPrefs().dsIsDrawPoint: DrawWidePoint(wp1[0],wp1[1],GetSkVecCol(sender.sockOutSk,2.2)); DrawWidePoint(wp2[0],wp2[1])
        MucDrawSk(sender.sockOutSk,sender.sockOutLH)
    else:
        DrawRectangleOnSocket(context,sender.sockOutSk,sender.sockOutLH,GetSkVecCol(sender.sockOutSk,2.2))
        DrawRectangleOnSocket(context,sender.sockInSk,sender.sockInLH,GetSkVecCol(sender.sockInSk,2.2))
        if DrawPrefs().dsIsColoredLine: col1 = GetSkCol(sender.sockOutSk); col2 = GetSkCol(sender.sockInSk)
        else: col1 = (1,1,1,1); col2 = (1,1,1,1)
        wp1 = PreparGetWP(sender.sockOutPs*uiFac[0],DrawPrefs().dsPointOffsetX); wp2 = PreparGetWP(sender.sockInPs*uiFac[0],-DrawPrefs().dsPointOffsetX)
        if DrawPrefs().dsIsDrawLine: DrawLine(wp1[0],wp2[0],lw,col1,col2)
        if DrawPrefs().dsIsDrawPoint: DrawWidePoint(wp1[0],wp1[1],GetSkVecCol(sender.sockOutSk,2.2)); DrawWidePoint(wp2[0],wp2[1],GetSkVecCol(sender.sockInSk,2.2))
        MucDrawSk(sender.sockOutSk,sender.sockOutLH); MucDrawSk(sender.sockInSk,sender.sockInLH)
class VoronoiLinker(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_linker'; bl_label = 'Voronoi Linker'; bl_options = {'UNDO'}
    def MucAssign(sender,context):
        muc = GetNearestSocketInRegionMouse(context,False,sender.sockOutSk); sender.sockInSk = muc[0]; sender.sockInPs = muc[1]; sender.sockInLH = muc[3]
        if (sender.sockOutSk!=None)and(sender.sockInSk!=None)and(sender.sockOutSk.node==sender.sockInSk.node):
            sender.sockInSk = None; sender.sockInPs = None; sender.sockInLH = None
        if (sender.sockOutSk)and(sender.sockOutSk.is_linked):
            for lk in sender.sockOutSk.links:
                if lk.to_socket==sender.sockInSk: sender.sockInSk = None; sender.sockInPs = None; sender.sockInLH = None
    def modal(self,context,event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE': VoronoiLinker.MucAssign(self,context)
            case 'RIGHTMOUSE'|'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle,'WINDOW')
                if (event.value=='RELEASE')and(self.sockOutSk!=None)and(self.sockInSk!=None):
                    tree = context.space_data.edit_tree
                    try: tree.links.new(self.sockOutSk,self.sockInSk)
                    except: pass #NodeSocketUndefined
                    if self.sockInSk.is_multi_input: #Если мультиинпут, то пережонглировать
                        skLinks = []
                        for lk in self.sockInSk.links: skLinks.append((lk.from_socket,lk.to_socket)); tree.links.remove(lk)
                        if self.sockOutSk.bl_idname=='NodeSocketVirtual': self.sockOutSk = self.sockOutSk.node.outputs[len(self.sockOutSk.node.outputs)-2]
                        tree.links.new(self.sockOutSk,self.sockInSk)
                        for cyc in range(0,len(skLinks)-1): tree.links.new(skLinks[cyc][0],skLinks[cyc][1])
                    return {'FINISHED'}
                else: return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self,context,event):
        context.area.tag_redraw(); NowTool[0] = 1
        if (context.area.type!='NODE_EDITOR')or(context.space_data.edit_tree==None): return {'CANCELLED'}
        else:
            muc = GetNearestSocketInRegionMouse(context,True,None); self.sockOutSk = muc[0]; self.sockOutPs = muc[1]; self.sockOutLH = muc[3]
            VoronoiLinker.MucAssign(self,context); uiFac[0] = uiScale(); where[0] = context.space_data; SetFont()
            self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiLinkerDrawCallback,(self,context),'WINDOW','POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}

def VoronoiMixerDrawCallback(sender,context):
    if where[0]!=context.space_data: return
    shader[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR'); shader[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR'); bgl.glHint(bgl.GL_LINE_SMOOTH_HINT,bgl.GL_NICEST)
    mousePos = context.space_data.cursor_location*uiFac[0]; mouseRegionPs = PosViewToReg(mousePos.x,mousePos.y); lw = DrawPrefs().dsLineWidth
    def MucDrawSk(Sk,lh,ys,lys):
        txtdim = DrawSkText(PosViewToReg(mousePos.x,mousePos.y),DrawPrefs().dsTextDistFromCursor,ys,Sk)
        if Sk.is_linked: DrawIsLinked(mousePos,txtdim[0],txtdim[1]*lys*.75,GetSkCol(Sk) if DrawPrefs().dsIsColoredMarker else (.9,.9,.9,1))
    if (sender.sockOut1Sk==None):
        if DrawPrefs().dsIsDrawPoint:
            wp1 = PreparGetWP(mousePos,-DrawPrefs().dsPointOffsetX*.75); wp2 = PreparGetWP(mousePos,DrawPrefs().dsPointOffsetX*.75)
            DrawWidePoint(wp1[0],wp1[1]); DrawWidePoint(wp2[0],wp2[1])
    elif (sender.sockOut1Sk!=None)and(sender.sockOut2Sk==None):
        DrawRectangleOnSocket(context,sender.sockOut1Sk,sender.sockOut1LH,GetSkVecCol(sender.sockOut1Sk,2.2))
        wp1 = PreparGetWP(sender.sockOut1Ps*uiFac[0],DrawPrefs().dsPointOffsetX); wp2 = PreparGetWP(mousePos,0); col = Vector((1,1,1,1))
        if DrawPrefs().dsIsDrawLine: DrawLine(wp1[0],mouseRegionPs,lw,GetSkCol(sender.sockOut1Sk) if DrawPrefs().dsIsColoredLine else col,col)
        if DrawPrefs().dsIsDrawPoint: DrawWidePoint(wp1[0],wp1[1],GetSkVecCol(sender.sockOut1Sk,2.2)); DrawWidePoint(wp2[0],wp2[1])
        MucDrawSk(sender.sockOut1Sk,sender.sockOut1LH,-.5,0)
    else:
        DrawRectangleOnSocket(context,sender.sockOut1Sk,sender.sockOut1LH,GetSkVecCol(sender.sockOut1Sk,2.2))
        DrawRectangleOnSocket(context,sender.sockOut2Sk,sender.sockOut2LH,GetSkVecCol(sender.sockOut2Sk,2.2))
        if DrawPrefs().dsIsColoredLine: col1 = GetSkCol(sender.sockOut1Sk); col2 = GetSkCol(sender.sockOut2Sk)
        else: col1 = (1,1,1,1); col2 = (1,1,1,1)
        wp1 = PreparGetWP(sender.sockOut1Ps*uiFac[0],DrawPrefs().dsPointOffsetX); wp2 = PreparGetWP(sender.sockOut2Ps*uiFac[0],DrawPrefs().dsPointOffsetX)
        if DrawPrefs().dsIsDrawLine: DrawLine(mouseRegionPs,wp2[0],lw,col2,col2); DrawLine(wp1[0],mouseRegionPs,lw,col1,col1)
        if DrawPrefs().dsIsDrawPoint: DrawWidePoint(wp1[0],wp1[1],GetSkVecCol(sender.sockOut1Sk,2.2)); DrawWidePoint(wp2[0],wp2[1],GetSkVecCol(sender.sockOut2Sk,2.2))
        MucDrawSk(sender.sockOut1Sk,sender.sockOut1LH,.25,1); MucDrawSk(sender.sockOut2Sk,sender.sockOut2LH,-1.25,-1)
class VoronoiMixer(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_mixer'; bl_label = 'Voronoi Mixer'; bl_options = {'UNDO'}
    def MucAssign(sender,context):
        muc = GetNearestSocketInRegionMouse(context,True,sender.sockOut1Sk); sender.sockOut2Sk = muc[0]; sender.sockOut2Ps = muc[1]; sender.sockOut2LH = muc[3]
        if (sender.sockOut1Sk!=None)and(sender.sockOut2Sk!=None)and(sender.sockOut1Sk==sender.sockOut2Sk): sender.sockOut2Sk = None; sender.sockOut2Ps = None
    def modal(self,context,event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE': VoronoiMixer.MucAssign(self,context)
            case 'RIGHTMOUSE'|'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle,'WINDOW')
                if (event.value=='RELEASE')and(self.sockOut1Sk!=None)and(self.sockOut2Sk!=None):
                    mixerSk1[0] = self.sockOut1Sk; mixerSk2[0] = self.sockOut2Sk; mixerSkTyp[0] = mixerSk1[0].type if mixerSk1[0].type!='CUSTOM' else mixerSk2[0].type
                    try:
                        dm = VMMapDictMain[context.space_data.tree_type][mixerSkTyp[0]]
                        if len(dm)!=0:
                            if (DrawPrefs().vmIsOneSkip)and(len(dm)==1): DoMix(context,dm[0])
                            else:
                                if DrawPrefs().vmMenuStyle=='Pie': bpy.ops.wm.call_menu_pie(name='node.VM_MT_voronoi_mixer_menu')
                                else: bpy.ops.wm.call_menu(name='node.VM_MT_voronoi_mixer_menu')
                    except: pass
                    return {'FINISHED'}
                else: return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self,context,event):
        context.area.tag_redraw(); NowTool[0] = 2
        if (context.area.type!='NODE_EDITOR')or(context.space_data.edit_tree==None): return {'CANCELLED'}
        else:
            muc = GetNearestSocketInRegionMouse(context,True,None); self.sockOut1Sk = muc[0]; self.sockOut1Ps = muc[1]; self.sockOut1LH = muc[3]
            VoronoiMixer.MucAssign(self,context); uiFac[0] = uiScale(); where[0] = context.space_data; SetFont()
            self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiMixerDrawCallback,(self,context),'WINDOW','POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
mixerSk1 = [None]; mixerSk2 = [None]; mixerSkTyp = [None]
VMMapDictMixersDefs = {
        'GeometryNodeSwitch':[-1,-1,'Switch'],'ShaderNodeMixShader':[1,2,'Mix'],'ShaderNodeAddShader':[0,1,'Add'],'ShaderNodeMixRGB':[1,2,'Mix RGB'],
        'ShaderNodeMath':[0,1,'Max'],'ShaderNodeVectorMath':[0,1,'Max'],'FunctionNodeBooleanMath':[0,1,'Or'],'FunctionNodeCompare':[-1,-1,'Compare'],
        'GeometryNodeCurveToMesh':[0,1,'Curve to Mesh'],'GeometryNodeInstanceOnPoints':[0,2,'Instance on Points'],'GeometryNodeMeshBoolean':[0,1,'Boolean'],
        'GeometryNodeStringJoin':[1,1,'Join'],'GeometryNodeJoinGeometry':[0,0,'Join'],'GeometryNodeGeometryToInstance':[0,0,'To Instance'],
        'CompositorNodeMixRGB':[1,2,'Mix'],'CompositorNodeMath':[0,1,'Max'],'CompositorNodeSwitch':[0,1,'Switch'],'CompositorNodeAlphaOver':[1,2,'Alpha Over'],
        'CompositorNodeSplitViewer':[0,1,'Split Viewer'],'CompositorNodeSwitchView':[0,1,'Switch View'],'TextureNodeMixRGB':[1,2,'Mix'],
        'TextureNodeMath':[0,1,'Max'],'TextureNodeTexture':[0,1,'Texture'],'TextureNodeDistance':[0,1,'Distance'],'ShaderNodeMix':[-1,-1,'Mix']}
VMMapDictSwitchType = {'VALUE':'FLOAT','INT':'FLOAT'}; VMMapDictUserSkName = {'VALUE':'Float','RGBA':'Color'}; VMMapDictMixInt = {'INT':'VALUE'}; 
def DoMix(context,who):
    tree = context.space_data.edit_tree
    if tree!=None:
        bpy.ops.node.add_node('INVOKE_DEFAULT',type=who,use_transform=True); aNd = tree.nodes.active; aNd.width = 140
        match aNd.bl_idname:
            case 'ShaderNodeMath'|'ShaderNodeVectorMath'|'CompositorNodeMath'|'TextureNodeMath': aNd.operation = 'MAXIMUM'
            case 'FunctionNodeBooleanMath': aNd.operation = 'OR'
            case 'TextureNodeTexture': aNd.show_preview = False
            case 'GeometryNodeSwitch': aNd.input_type = VMMapDictSwitchType.get(mixerSkTyp[0],mixerSkTyp[0])
            case 'FunctionNodeCompare': aNd.data_type = VMMapDictSwitchType.get(mixerSkTyp[0],mixerSkTyp[0]); aNd.operation = aNd.operation if aNd.data_type!='FLOAT' else 'EQUAL'
            case 'ShaderNodeMix': aNd.data_type = VMMapDictSwitchType.get(mixerSkTyp[0],mixerSkTyp[0])
        match aNd.bl_idname:
            case 'GeometryNodeSwitch'|'FunctionNodeCompare'|'ShaderNodeMix':
                tgl = aNd.bl_idname!='FunctionNodeCompare'
                foundSkList = [sk for sk in (reversed(aNd.inputs) if tgl else aNd.inputs) if sk.type==VMMapDictMixInt.get(mixerSkTyp[0],mixerSkTyp[0])]
                tree.links.new(mixerSk1[0],foundSkList[tgl]); tree.links.new(mixerSk2[0],foundSkList[not tgl])
            case _:
                if aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][0]].is_multi_input: tree.links.new(mixerSk2[0],aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][1]])
                tree.links.new(mixerSk1[0],aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][0]])
                if aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][0]].is_multi_input==False: tree.links.new(mixerSk2[0],aNd.inputs[VMMapDictMixersDefs[aNd.bl_idname][1]])
class VoronoiMixerMixer(bpy.types.Operator):
    bl_idname = 'node.voronoi_mixer_mixer'; bl_label = 'Voronoi Mixer Mixer'; bl_options = {'UNDO'}
    who: bpy.props.StringProperty()
    def execute(self,context):
        DoMix(context,self.who)
        return {'FINISHED'}
VMMapDictMain = {
        'ShaderNodeTree':{'SHADER':['ShaderNodeMixShader','ShaderNodeAddShader'],'VALUE':['ShaderNodeMix','ShaderNodeMixRGB','ShaderNodeMath'],
                'RGBA':['ShaderNodeMix','ShaderNodeMixRGB'],'VECTOR':['ShaderNodeMix','ShaderNodeMixRGB','ShaderNodeVectorMath'],'INT':['ShaderNodeMix','ShaderNodeMixRGB','ShaderNodeMath']},
        'GeometryNodeTree':{'VALUE':['GeometryNodeSwitch','ShaderNodeMixRGB','FunctionNodeCompare','ShaderNodeMath'],
                'RGBA':['GeometryNodeSwitch','ShaderNodeMixRGB','FunctionNodeCompare'],
                'VECTOR':['GeometryNodeSwitch','ShaderNodeMixRGB','FunctionNodeCompare','ShaderNodeVectorMath'],
                'STRING':['GeometryNodeSwitch','FunctionNodeCompare','GeometryNodeStringJoin'],
                'INT':['GeometryNodeSwitch','ShaderNodeMixRGB','FunctionNodeCompare','ShaderNodeMath'],
                'GEOMETRY':['GeometryNodeSwitch','GeometryNodeJoinGeometry','GeometryNodeInstanceOnPoints','GeometryNodeCurveToMesh','GeometryNodeMeshBoolean','GeometryNodeGeometryToInstance'],
                'BOOLEAN':['GeometryNodeSwitch','ShaderNodeMixRGB','ShaderNodeMath','FunctionNodeBooleanMath'],'OBJECT':['GeometryNodeSwitch'],
                'MATERIAL':['GeometryNodeSwitch'],'COLLECTION':['GeometryNodeSwitch'],'TEXTURE':['GeometryNodeSwitch'],'IMAGE':['GeometryNodeSwitch']},
        'CompositorNodeTree':{'VALUE':['CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView','CompositorNodeMath'],
                'RGBA':['CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView','CompositorNodeAlphaOver'],
                'VECTOR':['CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView'],
                'INT':['CompositorNodeMixRGB','CompositorNodeSwitch','CompositorNodeSplitViewer','CompositorNodeSwitchView','CompositorNodeMath']},
        'TextureNodeTree':{'VALUE':['TextureNodeMixRGB','TextureNodeMath','TextureNodeTexture'],'RGBA':['TextureNodeMixRGB','TextureNodeTexture'],
                'VECTOR':['TextureNodeMixRGB','TextureNodeDistance'],'INT':['TextureNodeMixRGB','TextureNodeMath','TextureNodeTexture']}}
class VoronoiMixerMenu(bpy.types.Menu):
    bl_idname = 'node.VM_MT_voronoi_mixer_menu'; bl_label = ''
    def draw(self,context):
        who = self.layout.menu_pie() if DrawPrefs().vmMenuStyle=='Pie' else self.layout
        who.label(text=VMMapDictUserSkName.get(mixerSkTyp[0],mixerSkTyp[0].capitalize()))
        for li in VMMapDictMain[context.space_data.tree_type][mixerSkTyp[0]]: who.operator('node.voronoi_mixer_mixer',text=VMMapDictMixersDefs[li][2]).who=li

def VoronoiPreviewerDrawCallback(sender,context):
    if where[0]!=context.space_data: return
    shader[0] = gpu.shader.from_builtin('2D_SMOOTH_COLOR'); shader[1] = gpu.shader.from_builtin('2D_UNIFORM_COLOR'); bgl.glHint(bgl.GL_LINE_SMOOTH_HINT,bgl.GL_NICEST)
    mousePos = context.space_data.cursor_location*uiFac[0]; mouseRegionPs = PosViewToReg(mousePos.x,mousePos.y); lw = DrawPrefs().dsLineWidth
    def MucDrawSk(Sk,lh):
        txtdim = DrawSkText(PosViewToReg(mousePos.x,mousePos.y),DrawPrefs().dsTextDistFromCursor,-.5,Sk)
        if Sk.is_linked: DrawIsLinked(mousePos,txtdim[0],0,GetSkCol(Sk) if DrawPrefs().dsIsColoredMarker else (.9,.9,.9,1))
    if (sender.sockOutSk==None):
        if DrawPrefs().dsIsDrawPoint: wp = PreparGetWP(mousePos,0); DrawWidePoint(wp[0],wp[1])
    else:
        DrawRectangleOnSocket(context,sender.sockOutSk,sender.sockOutLH,GetSkVecCol(sender.sockOutSk,2.2))
        col = GetSkCol(sender.sockOutSk) if DrawPrefs().dsIsColoredLine else (1,1,1,1); wp = PreparGetWP(sender.sockOutPs*uiFac[0],DrawPrefs().dsPointOffsetX)
        if DrawPrefs().dsIsDrawLine: DrawLine(wp[0],mouseRegionPs,lw,col,col)
        if DrawPrefs().dsIsDrawPoint: DrawWidePoint(wp[0],wp[1],GetSkVecCol(sender.sockOutSk,2.2))
        MucDrawSk(sender.sockOutSk,sender.sockOutLH)
class VoronoiPreviewer(bpy.types.Operator):
    bl_idname = 'node.a_voronoi_previewer'; bl_label = 'Voronoi Previewer'; bl_options = {'UNDO'}
    def MucAssign(sender,context):
        muc = GetNearestSocketInRegionMouse(context,True,None); sender.sockOutSk = muc[0]; sender.sockOutPs = muc[1]; sender.sockOutLH = muc[3]
        if (sender.sockOutSk)and(sender.sockOutSk.type=='CUSTOM'): sender.sockOutSk = None
        if (DrawPrefs().vpIsLivePreview)and(sender.sockOutSk!=None): VoronoiPreviewer_DoPreview(context,sender.sockOutSk)
    def modal(self,context,event):
        context.area.tag_redraw()
        match event.type:
            case 'MOUSEMOVE': VoronoiPreviewer.MucAssign(self,context)
            case 'LEFTMOUSE'|'RIGHTMOUSE'|'ESC':
                bpy.types.SpaceNodeEditor.draw_handler_remove(self._handle,'WINDOW')
                if (event.value=='RELEASE')and(self.sockOutSk!=None): VoronoiPreviewer_DoPreview(context,self.sockOutSk); return {'FINISHED'}
                else: return {'CANCELLED'}
        return {'RUNNING_MODAL'}
    def invoke(self,context,event):
        if (context.space_data.tree_type=='GeometryNodeTree')and('FINISHED' in bpy.ops.node.select('INVOKE_DEFAULT')): return {'PASS_THROUGH'}
        if (event.type=='RIGHTMOUSE')^DrawPrefs().vmPreviewHKInverse:
            nodes = context.space_data.edit_tree.nodes
            for nd in nodes: nd.select = False
            nnd = (nodes.get('Voronoi_Anchor') or nodes.new('NodeReroute'))
            nnd.name = 'Voronoi_Anchor'; nnd.label = 'Voronoi_Anchor'; nnd.location = context.space_data.cursor_location; nnd.select = True; return {'FINISHED'}
        else:
            context.area.tag_redraw(); NowTool[0] = 3
            if (context.area.type!='NODE_EDITOR')or(context.space_data.edit_tree==None): return {'CANCELLED'}
            else:
                VoronoiPreviewer.MucAssign(self,context); uiFac[0] = uiScale(); where[0] = context.space_data; SetFont()
                self._handle = bpy.types.SpaceNodeEditor.draw_handler_add(VoronoiPreviewerDrawCallback,(self,context),'WINDOW','POST_PIXEL')
                context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
ShaderShadersWithColor = ('BSDF_ANISOTROPIC','BSDF_DIFFUSE','EMISSION','BSDF_GLASS','BSDF_GLOSSY','BSDF_HAIR','BSDF_HAIR_PRINCIPLED','PRINCIPLED_VOLUME','BACKGROUND',
        'BSDF_REFRACTION','SUBSURFACE_SCATTERING','BSDF_TOON','BSDF_TRANSLUCENT','BSDF_TRANSPARENT','BSDF_VELVET','VOLUME_ABSORPTION','VOLUME_SCATTER')
def VoronoiPreviewer_DoPreview(context,goalSk):
    def GetSocketIndex(socket): return int(socket.path_from_id().split('.')[-1].split('[')[-1][:-1])
    def GetTreesWay(context,nd):
        way = []; nds = []; treeWyc = context.space_data.node_tree; lim = 0
        while (treeWyc!=context.space_data.edit_tree)and(lim<64):
            way.insert(0,treeWyc); nds.insert(0,treeWyc.nodes.active); treeWyc = treeWyc.nodes.active.node_tree; lim += 1
        way.insert(0,treeWyc); nds.insert(0,nd); return way, nds
    for ng in bpy.data.node_groups:
        if ng.type==context.space_data.node_tree.type:
            sk = ng.outputs.get('voronoi_preview')
            if sk!=None: ng.outputs.remove(sk)
    curTree = context.space_data.edit_tree
    WayTr, WayNd = GetTreesWay(context,goalSk.node); hWyLen = len(WayTr)-1; ixSkLastUsed = -1; isZeroPreviewGen = True
    for cyc in range(hWyLen+1):
        nodeIn = None; sockOut = None; sockIn = None
        #Найти принимающий нод текущего уровня
        if cyc!=hWyLen:
            for nd in WayTr[cyc].nodes:
                if nd.type in ['GROUP_OUTPUT','OUTPUT_MATERIAL','OUTPUT_WORLD','OUTPUT_LIGHT','COMPOSITE','OUTPUT']:
                    if nodeIn==None: nodeIn = nd
                    elif nodeIn.location>goalSk.node.location: nodeIn = nd
        else:
            match context.space_data.tree_type:
                case 'ShaderNodeTree':
                    num = int(goalSk.node.type in ('VOLUME_ABSORPTION','VOLUME_SCATTER','PRINCIPLED_VOLUME'))
                    for nd in WayTr[hWyLen].nodes:
                        if nd.type in ['OUTPUT_MATERIAL','OUTPUT_WORLD','OUTPUT_LIGHT','OUTPUT']:
                            sockIn = nd.inputs[num*(not(nd.type in ['OUTPUT_WORLD','OUTPUT_LIGHT','OUTPUT']))] if nd.is_active_output else sockIn
                case 'CompositorNodeTree':
                    for nd in WayTr[hWyLen].nodes: sockIn = nd.inputs[0] if (nd.type=='VIEWER') else sockIn
                    if sockIn==None:
                        for nd in WayTr[hWyLen].nodes: sockIn = nd.inputs[0] if (nd.type=='COMPOSITE')and(nd.is_active_output) else sockIn
                case 'GeometryNodeTree':
                    for nd in WayTr[hWyLen].nodes:
                        sockIn = nd.inputs.get('Geometry') if (nd.type=='GROUP_OUTPUT')and(nd.is_active_output) else sockIn
                        lis = [sk for sk in nd.inputs if sk.type=='GEOMETRY']; sockIn = lis[0] if (sockIn==None)and(len(lis)!=0) else sockIn
                        if sockIn==None:
                            try: sockIn = nd.inputs[0]
                            except: pass
                case 'TextureNodeTree':
                    for nd in WayTr[hWyLen].nodes: sockIn = nd.inputs[0] if (nd.type=='OUTPUT')and(nd.is_active_output) else sockIn
            nodeIn = sockIn.node
        #Определить сокет отправляющего нода
        if cyc==0: sockOut = goalSk
        else: sockOut = WayNd[cyc].outputs.get('voronoi_preview'); sockOut = WayNd[cyc].outputs[ixSkLastUsed] if sockOut==None else sockOut
        #Определить сокет принимающего нода:
        for sl in sockOut.links:
            if sl.to_node==nodeIn: sockIn = sl.to_socket; ixSkLastUsed = GetSocketIndex(sockIn)
        if sockIn==None:
            sockIn = WayTr[cyc].outputs.get('voronoi_preview')
            if sockIn==None:
                txt = 'NodeSocketColor' if context.space_data.tree_type!='GeometryNodeTree' else 'NodeSocketGeometry'
                txt = 'NodeSocketShader' if sockOut.type=='SHADER' else txt
                WayTr[cyc].outputs.new(txt,'voronoi_preview')
                if nodeIn==None: nodeIn = WayTr[cyc].nodes.new('NodeGroupOutput'); nodeIn.location = WayNd[cyc].location; nodeIn.location.x += WayNd[cyc].width*2
                sockIn = nodeIn.inputs.get('voronoi_preview'); sockIn.hide_value = True; isZeroPreviewGen = False
        #Удобный сразу-в-шейдер
        if (sockOut.type in ('RGBA'))and(cyc==hWyLen)and(len(sockIn.links)!=0)and(sockIn.links[0].from_node.type in ShaderShadersWithColor)and(isZeroPreviewGen):
            if len(sockIn.links[0].from_socket.links)==1: sockIn = sockIn.links[0].from_node.inputs.get('Color')
        #Соеденить:
        nd_va = WayTr[cyc].nodes.get('Voronoi_Anchor')
        if nd_va==None:
            if (sockOut!=None)and(sockIn!=None)and((sockIn.name=='voronoi_preview')or(cyc==hWyLen)): WayTr[cyc].links.new(sockOut,sockIn)
        else: WayTr[cyc].links.new(sockOut,nd_va.inputs[0])
    #Выделить предпросматриваемый нод:
    if DrawPrefs().vpSelectPreviewedNode:
        for nd in curTree.nodes: nd.select = False
        curTree.nodes.active = goalSk.node; goalSk.node.select = True

class VoronoiAddonPrefs(bpy.types.AddonPreferences):
    bl_idname = __name__ if __name__!='__main__' else 'VoronoiLinker'
    dsLineWidth: bpy.props.IntProperty(name='Line Width',default=1,min=1,max=16,subtype='FACTOR')
    dsPointOffsetX: bpy.props.FloatProperty(name='Point offset X',default=20,min=-50,max=50)
    dsPointResolution: bpy.props.IntProperty(name='Point resolution',default=54,min=3,max=64)
    dsPointRadius: bpy.props.FloatProperty(name='Point radius scale',default=1,min=0,max=3)
    dsIsDrawSkText: bpy.props.BoolProperty(name='Draw Text',default=True); dsIsColoredText: bpy.props.BoolProperty(name='Colored Text',default=True)
    dsIsDrawMarker: bpy.props.BoolProperty(name='Draw Marker',default=True); dsIsColoredMarker: bpy.props.BoolProperty(name='Colored Marker',default=True)
    dsIsDrawPoint: bpy.props.BoolProperty(name='Draw Points',default=True); dsIsColoredPoint: bpy.props.BoolProperty(name='Colored Points',default=True)
    dsIsDrawLine: bpy.props.BoolProperty(name='Draw Line',default=True); dsIsColoredLine: bpy.props.BoolProperty(name='Colored Line',default=True)
    dsIsDrawArea: bpy.props.BoolProperty(name='Draw Socket Area',default=True); dsIsColoredArea: bpy.props.BoolProperty(name='Colored Socket Area',default=True)
    dsTextStyle: bpy.props.EnumProperty(name='Text Style',default='Classic',items={('Classic','Classic',''),('Simplified','Simplified',''),('Text','Only text','')})
    dsIsAlwaysLine: bpy.props.BoolProperty(name='Always draw line for VoronoiLinker',default=False)
    vmPreviewHKInverse: bpy.props.BoolProperty(name='Previews hotkey inverse',default=False)
    vmIsOneSkip: bpy.props.BoolProperty(name='One Choise to skip',default=True,description='If the selection contains a single element, skip the selection and add it immediately')
    vmMenuStyle: bpy.props.EnumProperty(name='Mixer Menu Style',default='Pie',items={('Pie','Pie',''),('List','List','')})
    vpIsLivePreview: bpy.props.BoolProperty(name='Live Preview',default=True)
    vpSelectPreviewedNode: bpy.props.BoolProperty(name='Select Previewed Node',default=True,description='Select and set acttive for node that was used by VoronoiPreview')
    dsTextFrameOffset: bpy.props.IntProperty(name='Text Frame Offset',default=0,min=0,max=24,subtype='FACTOR')
    dsFontSize: bpy.props.IntProperty(name='Text Size',default=28,min=10,max=48)
    aDisplayAdvanced: bpy.props.BoolProperty(name='Display advanced options',default=False)
    dsTextDistFromCursor: bpy.props.FloatProperty(name='Text distance from cursor',default=25,min=5,max=50)
    dsTextLineframeOffset: bpy.props.FloatProperty(name='Text Line-frame offset',default=2,min=0,max=10)
    dsIsDrawSkTextShadow: bpy.props.BoolProperty(name='Draw Text Shadow',default=True)
    dsShadowCol: bpy.props.FloatVectorProperty(name='Shadow Color',default=[0.0,0.0,0.0,.5],size=4,min=0,max=1,subtype='COLOR')
    dsShadowOffset: bpy.props.IntVectorProperty(name='Shadow Offset',default=[2,-2],size=2,min=-20,max=20)
    dsShadowBlur: bpy.props.IntProperty(name='Shadow Blur',default=2,min=0,max=2)
    dsIsDrawDebug: bpy.props.BoolProperty(name='draw debug',default=False)
    def draw(self,context):
        col0 = self.layout.column(); box = col0.box(); col1 = box.column(align=True); col1.label(text='Draw setiings:')
        col1.prop(self,'dsPointOffsetX'); col1.prop(self,'dsTextFrameOffset'); col1.prop(self,'dsFontSize'); box = col1.box(); box.prop(self,'aDisplayAdvanced')
        if self.aDisplayAdvanced:
            col2 = box.column(); col3 = col2.column(align=True); col3.prop(self,'dsLineWidth'); col3.prop(self,'dsPointRadius'); col3.prop(self,'dsPointResolution')
            col3 = col2.column(align=True); col3.prop(self,'dsTextDistFromCursor'); col3.prop(self,'dsTextLineframeOffset'); col3 = col2.column(align=True)
            box = col2.box(); col4 = box.column(); col4.prop(self,'dsIsDrawSkTextShadow')
            if self.dsIsDrawSkTextShadow:
                row = col4.row(align=True); row.prop(self,'dsShadowCol'); row = col4.row(align=True); row.prop(self,'dsShadowOffset'); col4.prop(self,'dsShadowBlur')
            col2.prop(self,'dsIsDrawDebug')
        row = col1.row(align=True); row.prop(self,'dsIsDrawSkText'); row.prop(self,'dsIsColoredText')
        row = col1.row(align=True); row.prop(self,'dsIsDrawMarker'); row.prop(self,'dsIsColoredMarker')
        row = col1.row(align=True); row.prop(self,'dsIsDrawPoint'); row.prop(self,'dsIsColoredPoint')
        row = col1.row(align=True); row.prop(self,'dsIsDrawLine'); row.prop(self,'dsIsColoredLine')
        row = col1.row(align=True); row.prop(self,'dsIsDrawArea'); row.prop(self,'dsIsColoredArea')
        col1.prop(self,'dsTextStyle'); col1.prop(self,'dsIsAlwaysLine')
        box = col0.box(); col1 = box.column(align=True); col1.label(text='Mixer setiings:'); col1.prop(self,'vmMenuStyle'); col1.prop(self,'vmIsOneSkip')
        box = col0.box(); col1 = box.column(align=True); col1.label(text='Preview setiings:')
        col1.prop(self,'vpIsLivePreview'); col1.prop(self,'vpSelectPreviewedNode'); col1.prop(self,'vmPreviewHKInverse')


classes = [VoronoiLinker,VoronoiMixer,VoronoiMixerMixer,VoronoiMixerMenu,VoronoiPreviewer,VoronoiAddonPrefs]
kmi_defs = (
    (VoronoiLinker.bl_idname,'RIGHTMOUSE',False,False,True),
    (VoronoiMixer.bl_idname,'RIGHTMOUSE',True,False,True),
    (VoronoiPreviewer.bl_idname,'LEFTMOUSE',True,True,False),
    (VoronoiPreviewer.bl_idname,'RIGHTMOUSE',True,True,False))
addon_keymaps = []
def register():
    for cl in classes: bpy.utils.register_class(cl)
    km = bpy.context.window_manager.keyconfigs.addon.keymaps.new(name='Node Editor',space_type='NODE_EDITOR')
    for (bl_id,key,Shift,Ctrl,Alt) in kmi_defs: kmi = km.keymap_items.new(idname=bl_id,type=key,value='PRESS',shift=Shift,ctrl=Ctrl,alt=Alt); addon_keymaps.append((km,kmi))
def unregister():
    for cl in reversed(classes): bpy.utils.unregister_class(cl)
    for km,kmi in addon_keymaps: km.keymap_items.remove(kmi)
    addon_keymaps.clear()


if __name__=='__main__': register()
