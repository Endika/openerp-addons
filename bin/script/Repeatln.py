import uno
import string
import unohelper
import xmlrpclib
from com.sun.star.task import XJobExecutor
if __name__<>"package":
    from lib.gui import *
    from lib.error import ErrorDialog
    from lib.functions import *
    from ServerParameter import *
    from LoginTest import *
    database="db_test002"
    uid = 3


#class RepeatIn:
class RepeatIn( unohelper.Base, XJobExecutor ):
    def __init__(self,sObject="",sVariable="",sFields="",sDisplayName="",bFromModify=False):
        # Interface Design
        LoginTest()

        if not loginstatus and __name__=="package":
            exit(1)

        self.win = DBModalDialog(60, 50, 180, 250, "RepeatIn Builder")
        self.win.addFixedText("lblVariable", 2, 12, 60, 15, "Objects to loop on :")
        self.win.addComboBox("cmbVariable", 180-120-2, 10, 120, 15,True, itemListenerProc=self.cmbVariable_selected)
        self.insVariable = self.win.getControl( "cmbVariable" )

        self.win.addFixedText("lblFields", 10, 32, 60, 15, "Field to loop on :")
        self.win.addComboListBox("lstFields", 180-120-2, 30, 120, 150, False,itemListenerProc=self.lstbox_selected)
        self.insField = self.win.getControl( "lstFields" )

        self.win.addFixedText("lblName", 12, 187, 60, 15, "Variable name :")
        self.win.addEdit("txtName", 180-120-2, 185, 120, 15,)

        self.win.addFixedText("lblUName", 8, 207, 60, 15, "Displayed name :")
        self.win.addEdit("txtUName", 180-120-2, 205, 120, 15,)

        self.win.addButton('btnOK',-2 ,-10,45,15,'Ok', actionListenerProc = self.btnOkOrCancel_clicked )

        self.win.addButton('btnCancel',-2 - 45 - 5 ,-10,45,15,'Cancel', actionListenerProc = self.btnOkOrCancel_clicked )
        # Variable Declaration
        self.sValue=None
        self.sObj=None
        self.aSectionList=[]
        self.sGVariable=sVariable
        self.sGDisplayName=sDisplayName
        self.aItemList=[]
        self.aComponentAdd=[]
        self.aObjectList=[]
        self.aListRepeatIn=[]
        self.aVariableList=[]
        # Call method to perform Enumration on Report Document
        EnumDocument(self.aItemList,self.aComponentAdd)
        # Perform checking that Field-1 and Field - 4 is available or not alos get Combobox
        # filled if condition is true
        desktop = getDesktop()
        doc = desktop.getCurrentComponent()
        docinfo = doc.getDocumentInfo()
        # Check weather Field-1 is available if not then exit from application
        self.sMyHost= ""

        if not docinfo.getUserFieldValue(3) == "" and not docinfo.getUserFieldValue(0)=="":
            self.sMyHost= docinfo.getUserFieldValue(0)
            self.count=0
            oParEnum = doc.getTextFields().createEnumeration()

            while oParEnum.hasMoreElements():
                oPar = oParEnum.nextElement()
                if oPar.supportsService("com.sun.star.text.TextField.DropDown"):
                    self.count += 1

            getList(self.aObjectList, self.sMyHost,self.count)
            cursor = doc.getCurrentController().getViewCursor()
            text = cursor.getText()
            tcur = text.createTextCursorByRange(cursor)

	    self.aVariableList.extend( filter( lambda obj: obj[:obj.find(" ")] == "List", self.aObjectList ) )

	    for i in range(len(self.aItemList)):
		anItem = self.aItemList[i][1]
		component = self.aComponentAdd[i]

		if component == "Document":
		    sLVal = anItem[anItem.find(",'") + 2:anItem.find("')")]
		    self.aVariableList.extend( filter( lambda obj: obj[:obj.find("(")] == sLVal, self.aObjectList ) )

                if tcur.TextSection:
                    getRecersiveSection(tcur.TextSection,self.aSectionList)
		    if component in self.aSectionList:
			sLVal = anItem[anItem.find(",'") + 2:anItem.find("')")]
			self.aVariableList.extend( filter( lambda obj: obj[:obj.find("(")] == sLVal, self.aObjectList ) )

                if tcur.TextTable:
		    if not component == "Document" and component[component.rfind(".") + 1:] == tcur.TextTable.Name:
			VariableScope( tcur, self.insVariable, self.aObjectList, self.aComponentAdd, self.aItemList, component )

            self.bModify=bFromModify

            if self.bModify==True:

                if sObject=="":
                    self.insVariable.setText("List of "+docinfo.getUserFieldValue(3))
                    self.insField.addItem("objects",self.win.getListBoxItemCount("lstFields"))
                    self.win.setEditText("txtName", sVariable)
                    self.win.setEditText("txtUName",sDisplayName)
                    self.sValue= "objects"
                else:
                    sItem=""
		    for anObject in self.aObjectList:
			if anObject[:anObject.find("(")] == sObject:
			    sItem = anObject
			    self.insVariable.setText( sItem )

		    genTree(
			sItem[sItem.find("(")+1:sItem.find(")")], 
			self.aListRepeatIn, 
			self.insField, 
			self.sMyHost, 
			2, 
			ending=['one2many','many2many'], 
			recur=['one2many','many2many']
		    )

                    self.sValue= self.win.getListBoxItem("lstFields",self.aListRepeatIn.index(sFields))

            for var in self.aVariableList:
                sock = xmlrpclib.ServerProxy(self.sMyHost + '/xmlrpc/object')
		if var[:8] <> 'List of ':
		    self.model_ids = sock.execute(database, uid, docinfo.getUserFieldValue(1), 'ir.model' ,  'search', [('model','=',var[var.find("(")+1:var.find(")")])])
                else:
		    self.model_ids = sock.execute(database, uid, docinfo.getUserFieldValue(1), 'ir.model' ,  'search', [('model','=',var[8:])])
                fields=['name','model']
                self.model_res = sock.execute(database, uid, docinfo.getUserFieldValue(1), 'ir.model', 'read', self.model_ids,fields)
                print self.model_res
                if self.model_res <> []:
		    if var[:8]<>'List of ':
                        self.insVariable.addItem(var[:var.find("(")+1] + self.model_res[0]['name'] + ")" ,self.insVariable.getItemCount())
                    else:
                        self.insVariable.addItem('List of ' + self.model_res[0]['name'] ,self.insVariable.getItemCount())
                else:
                    self.insVariable.addItem(var ,self.insVariable.getItemCount())

            self.win.doModalDialog("lstFields",self.sValue)
        else:
            ErrorDialog("Please Select Appropriate module" ,"Create new report from: \nTiny Report->Open a New Report")
            self.win.endExecute()

    def lstbox_selected(self,oItemEvent):
        sItem=self.win.getListBoxSelectedItem("lstFields")
        sMain=self.aListRepeatIn[self.win.getListBoxSelectedItemPos("lstFields")]

        if self.bModify==True:
            self.win.setEditText("txtName", self.sGVariable)
            self.win.setEditText("txtUName",self.sGDisplayName)
        else:
	    self.win.setEditText("txtName",sMain[sMain.rfind("/")+1:])
	    self.win.setEditText("txtUName","|-."+sItem[sItem.rfind("/")+1:]+".-|")

    def cmbVariable_selected(self,oItemEvent):

        if self.count > 0 :
            sock = xmlrpclib.ServerProxy(self.sMyHost + '/xmlrpc/object')
            desktop=getDesktop()
            doc =desktop.getCurrentComponent()
            docinfo=doc.getDocumentInfo()
            self.win.removeListBoxItems("lstFields", 0, self.win.getListBoxItemCount("lstFields"))
            sItem=self.win.getComboBoxText("cmbVariable")
            for var in self.aVariableList:
		if var[:8]=='List of ':
		    if var[:8]==sItem[:8]:
                        sItem = var
		elif var[:var.find("(")+1] == sItem[:sItem.find("(")+1]:
                    sItem = var
            self.aListRepeatIn=[]

	    data = ( sItem[sItem.rfind(" ") + 1:] == docinfo.getUserFieldValue(3) ) and docinfo.getUserFieldValue(3) or sItem[sItem.find("(")+1:sItem.find(")")] 
	    genTree( data, self.aListRepeatIn, self.insField, self.sMyHost, 2, ending=['one2many','many2many'], recur=['one2many','many2many'] )

            self.win.selectListBoxItemPos("lstFields", 0, True )

        else:
            sItem=self.win.getComboBoxText("cmbVariable")
            for var in self.aVariableList:
		if var[:8]=='List of ' and var[:8] == sItem[:8]:
		    sItem = var
	    self.win.setEditText("txtName",sItem[sItem.rfind(".")+1:])
	    self.win.setEditText("txtUName","|-."+sItem[sItem.rfind(".")+1:]+".-|")
            self.insField.addItem("objects",self.win.getListBoxItemCount("lstFields"))
            self.win.selectListBoxItemPos("lstFields", 0, True )

    def btnOkOrCancel_clicked(self, oActionEvent):
        if oActionEvent.Source.getModel().Name == "btnOK":
            desktop=getDesktop()
            doc = desktop.getCurrentComponent()
            cursor = doc.getCurrentController().getViewCursor()

	    selectedItem = self.win.getListBoxSelectedItem( "lstFields" )
	    selectedItemPos = self.win.getListBoxSelectedItemPos( "lstFields" )
	    txtName = self.win.getEditText( "txtName" )
	    txtUName = self.win.getEditText( "txtUName" )

            if selectedItem != "" and txtName != "" and txtUName != "":
		sKey=u""+ txtUName
		if selectedItem == "objects":
		    sValue=u"[[ repeatIn(" + selectedItem + ",'" + txtName + "') ]]"
		else:
		    sObjName=self.win.getComboBoxText("cmbVariable")
		    sObjName=sObjName[:sObjName.find("(")]
		    sValue=u"[[ repeatIn(" + sObjName + self.aListRepeatIn[selectedItemPos].replace("/",".") + ",'" + txtName +"') ]]"

		if self.bModify == True:
		    oCurObj = cursor.TextField
		    oCurObj.Items = (sKey,sValue)
		    oCurObj.update()
		else:
                    oInputList = doc.createInstance("com.sun.star.text.TextField.DropDown")
		    oInputList.Items = (sKey,sValue)
		    widget = ( cursor.TextTable or selectedItem <> 'object' ) and cursor.TextTable.getCellByName( cursor.cell.CellName ) or doc.Text
		    widget.insertTextContent(cursor,oInputList,False)

                self.win.endExecute()
            else:
                ErrorDialog("Please Fill appropriate data in Object Field or Name field \nor select perticular value from the list of fields")

        elif oActionEvent.Source.getModel().Name == "btnCancel":
            self.win.endExecute()

if __name__<>"package" and __name__=="__main__":
    RepeatIn()
elif __name__=="package":
    g_ImplementationHelper = unohelper.ImplementationHelper()
    g_ImplementationHelper.addImplementation( RepeatIn, "org.openoffice.tiny.report.repeatln", ("com.sun.star.task.Job",),) 
