import netsvc
from osv import fields, osv
import pooler

import imaplib
import poplib

class webmail_tiny_user(osv.osv):
    _name="webmail.tiny.user"
    _description="User Configuration"
    _rec_name="user_id"
    _columns={
        'user_id' : fields.many2one('res.users', 'User'),
        'server_conf_id':fields.one2many('webmail.server','server_id','Configuration')
    }
    _default={
        'user_id': lambda obj, cr, uid, context: uid,
    }
webmail_tiny_user()

class webmail_server(osv.osv):
    _name="webmail.server"
    _description="Mail Server Configuration"
    _columns={
        'name': fields.char("Name", size=64, required=True),
        'iserver_name': fields.char('Server Name', size=64, required=True),
        'iserver_type': fields.selection([('imap','IMAP'),('pop3','POP3')], 'Server Type'),
        'iuser_name':fields.char('User Name', size=64, required=True),
        'ipassword':fields.char('Password', size=64, required=True),
        'iconn_type':fields.boolean('SSL'),        
        'iconn_port':fields.integer('Port'),
        'oserver_name': fields.char('Server Name', size=64, required=True),
        'ouser_name':fields.char('User Name', size=64, required=True),
        'opassword':fields.char('Password', size=64, required=True),
        'oconn_type':fields.boolean('SSL'),
        'oconn_port':fields.integer('Port'),
        'server_id':fields.many2one('webmail.tiny.user',"Mail Client"),
    }
    _default={
        'oconn_port': lambda *a: 25,
    }
    
    def _login(self, cr, uid, ids, context, server, port, ssl, type, user, password):
        server = self.browse(cr, uid, ids[0])
        obj = None
        try:
            if type=='imap':
                if ssl:
                    obj = poplib.IMAP4_SSL(server, port)
                else:
                    obj = poplib.IMAP4(server, port)
            else:
                if ssl:
                    obj = poplib.POP3_SSL(server, port)
                else:
                    obj = poplib.POP3(server, port)                    
            obj.login(server.iuser_name, server.ipassword)            
        except Exception,e:
            pass
        return obj
        
    def _test_connection(self, cr, uid, ids, context):
        server = self.browse(cr, uid, ids[0])
        obj = self._login(cr, uid, ids, context, server.iserver_name, server.iconn_port, server.iconn_type, server.iserver_type, server.iuser_name, server.ipassword)
        if not obj:
           raise osv.except_osv(
                        'Connection Error !',
                        'Please enter valid server information.')
        else:
            raise osv.except_osv(
                        'Connection!',
                        'Connection done successfully.')        
        return True
        
webmail_server()

class webmail_mailbox(osv.osv):
    _name="webmail.mailbox"
    _description="User Mailbox"
    _columns={
        'user_id': fields.many2one('res.users', 'User'),
        'name': fields.char('Name', size=64, required=True),
        'parent_id': fields.many2one('webmail.mailbox','Parent Folder', select=True),
        'child_id': fields.one2many('webmail.mailbox', 'parent_id', string='Child Folder'),
        'account_id': fields.many2one('webmail.server', 'Server'),
    }
    _default={
        'user_id': lambda obj, cr, uid, context: uid,
    }
    
    def _select(self, cr, uid, ids, context, mail_acc):
        server_obj = pooler.get_pool(cr.dbname).get('webmail.server')
        obj = server_obj._login(cr, uid, ids, context, mail_acc.iserver_name, mail_acc.iconn_port, mail_acc.iconn_type, mail_acc.iserver_type, mail_acc.iuser_name, mail_acc.ipassword)
        return obj.select()[1]
        
    def _new(self, cr, uid, ids, context, name):
         mailbox_obj = self.pool.get('webmail.mailbox')
         server_obj = self.pool.get('webmail.server')
         
         mailbox = mailbox_obj.browse(cr, uid, ids[0])
         server = server_obj.browse(cr, uid, mailbox.account_id.id)
         if server.iserver_type=='imap':
             obj = server._login(cr, uid, ids, context, server.iserver_name, server.iconn_port, server.iconn_type, server.iserver_type, server.iuser_name, server.ipassword)
             if obj:
                obj.create(name)
                mailbox_obj.create(cr, uid, {'name':name, 'parent_id':mailbox.parent_id})
    
    def _rename(self, cr, uid, ids, context, old, new):
        mailbox_obj = self.pool.get('webmail.mailbox')
        server_obj = self.pool.get('webmail.server')
        
        mailbox = mailbox_obj.browse(cr, uid, ids[0])
        server = server_obj.browse(cr, uid, mailbox.account_id.id)
        if server.iserver_type=='imap':
            obj = server._login(cr, uid, ids, context, server.iserver_name, server.iconn_port, server.iconn_type, server.iserver_type, server.iuser_name, server.ipassword)
            if obj:
                obj.rename(old, new)
                mailbox_obj.write(cr, uid, ids, {'name': new_name })    
    
    def _delete(self, cr, uid, ids, context):
        mailbox_obj = self.pool.get('webmail.mailbox')
        server_obj = self.pool.get('webmail.server')
        
        mailbox = mailbox_obj.browse(cr, uid, ids[0])
        server = server_obj.browse(cr, uid, mailbox.account_id.id)
        if server.iserver_type=='imap':
            obj = server._login(cr, uid, ids, context, server.iserver_name, server.iconn_port, server.iconn_type, server.iserver_type, server.iuser_name, server.ipassword)
            if obj:
                obj.delete(mailbox.name)
                mailbox_obj.unlink(cr, uid, ids)
                
    def _fetch_mail(self, cr, uid, ids, context):
        pass
    
webmail_mailbox()

class webmail_tags(osv.osv):
    _name="webmail.tags"
    _description="Email Tag"
    _columns={
        'user_id': fields.many2one('res.users', 'User'),
        'name': fields.char('Tag Name', size=128),        
        'account_id': fields.many2one('webmail.server', 'Server'),
    }
    _default={
        'user_id': lambda obj, cr, uid, context: uid,
        'account_id': lambda obj, cr, uid, context: context.get('account_id',False),
    }
webmail_tags()

class webmail_email(osv.osv):
    _name="webmail.email"
    _description="User Email"
    _columns={
        'user_id': fields.many2one('res.users', 'User'),
        'account_id': fields.many2one('webmail.server', 'Server'),
        'folder_id': fields.many2one('webmail.mailbox', 'Folder'),
        'message_id': fields.char('Message Id',size=256),
        'active': fields.boolean('Active'),
        'from_user': fields.char('From', size=256),
        'to': fields.char('To', size=256),
        'subject': fields.char('Subject', size=256),
        'date': fields.datetime('Date'),
        'cc': fields.char('Cc', size=256),
        'bcc': fields.char('Bcc', size=256),
        'body': fields.text('Body'),
        'attachment_id': fields.one2many('webmail.email.attachment', 'email_id', string='Attachment'),
        'tag_id': fields.many2one('webmail.tags', 'Tags'),
    }
    _default={
        'user_id': lambda obj, cr, uid, context: uid,
    }
    
    def default_get(self, cr, uid, fields, context={}):
        data = super(webmail_email,self).default_get(cr, uid, fields, context)
        if context.has_key('mailid') and context.has_key('action'):
            id = context.get('mailid',False)
            action = context.get('action',False)
            if id and action:
                mail = self.browse(cr, uid, id)
                if action=='reply':
                    data['to']=mail.from_user
                elif action=='replyall':
                    data['to']=mail.from_user
                    if mail.cc:
                        data['cc']=mail.cc
                    if mail.bcc:
                        data['bcc']=mail.bcc
        return data
     
    def _send_mail(self, cr, uid, ids, context):
        pass
    
webmail_email()

class webmail_email_attachment(osv.osv):
    _name="webmail.email.attachment"
    _description="Attachment"
    _rec_name="attachment"
    _columns={
        'user_id': fields.many2one('res.users', 'User'),
        'email_id': fields.many2one('webmail.email', 'Email'),
        'attachment': fields.binary('Attachment'),
        'name': fields.char('File Name',size=128)
    }
    _default={
        'user_id': lambda obj, cr, uid, context: uid,
    }
webmail_email_attachment()
