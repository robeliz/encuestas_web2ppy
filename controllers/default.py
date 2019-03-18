# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
# ENCUESTAS
# -------------------------------------------------------------------------

def encuesta_list():
    encuestas = db(db.encuestas).select()
    return dict(encuestas=encuestas)

def responde_encuesta():
    encuesta = db.encuestas(request.args(0, cast=int))
    preguntas = db(db.preguntas.encuesta == encuesta.id).select()
    return dict(e=encuesta, p=preguntas)

def elimina_encuesta():
    id_encuesta = request.args(0, cast=int);
    encuesta = db.encuestas(id_encuesta)

    if not encuesta:
        session.flash='Encuesta no encontrada'
    else:
        session.flash='Encuesta eliminada'
        encuesta.delete_record()


    redirect(URL('index'))

    return dict()

def analiza_encuesta():
    # solo lee la encuesta el usuario que la crea
    if not auth.user:
        session.flash = 'Solo disponible para su autor'
        redirect(URL('index'))

    id_encuesta = request.args(0, cast=int)
    encuesta = db.encuesta(id_encuesta) or redirect(URL('index'))
    respuestas = db(db.respuesta.encuesta == id_encuesta).select()

    # si no hay respuestas no tiene sentido
    if not respuestas:
        session.flash = 'No hay respuestas'
        redirect(URL('index'))

    # desde una conexión local
    if auth.user.id != encuesta.created_by:
        session.flash = 'Solo disponible para su autor'
        redirect(URL('index'))

    preguntas = db(db.pregunta.encuesta == id_encuesta).select()

    return dict(encuesta=encuesta, preguntas=preguntas, respuestas=respuestas)

def responde_encuesta():
    usuario = request.client
    id_encuesta = request.args(0, cast=int)
    respuesta = db((db.respuestas.encuesta == id_encuesta) &
                   (db.respuestas.usuario == usuario)).select().first()

    if respuesta:
        session.flash = 'Ya has respondido a esa encuesta'
        redirect(URL('index'))

    encuesta = db.encuestas(id_encuesta) or redirect(URL('index'))
    preguntas = db(db.preguntas.encuesta == id_encuesta).select()

    inputs = [INPUT(_type='radio',
                    _name=f'pregunta-{pregunta.id}',
                    _value=idx,
                    requires=IS_NOT_EMPTY())
              for pregunta in preguntas
              for idx, opcion in enumerate(pregunta.respuesta_text)]

    form = FORM(*inputs)

    if form.process().accepted:
        response.flash='Ok'
        # incrementa los acumulados de cada pregunta
        for row in preguntas:
            opcion = int(form.vars.get('pregunta-' + str(row.id)))
            acus = row.acumulados
            acus[opcion] += 1
            #logger.debug(f'{row.id}: {acus}')
            row.update_record(acumulados=acus)
        # guarda la respuesta
        db.respuestas.insert(encuesta=id_encuesta)
        redirect(URL('index'))

    return dict(encuesta=encuesta, preguntas=preguntas, form=form)

def analiza_encuesta():
    return dict()

# ---- example index page ----
def index():
    links = [lambda row: A('responder',
                           _href=URL('responde_encuesta', args=row.id),
                           _class='btn btn-primary')]
    if auth.user:
        links.append(lambda row: A('analizar',
                                   _href=URL('analiza_encuesta', args=row.id),
                                   _class='btn btn-primary'))
        links.append(lambda row: A('editar',
                                   _href=URL('edita_encuesta', args=row.id),
                                   _class='btn btn-primary'))
        links.append(lambda row: A('eliminar',
                                   _href=URL('elimina_encuesta', args=row.id),
                                   _class='btn btn-danger'))

    db.encuestas.id.readable = False
    db.encuestas.id.writable = False
    grid = SQLFORM.grid(db.encuestas,
                        # searchable=False,
                        create=False,
                        editable=False,
                        deletable=False,
                        details=False,
                        csv=False,
                        links=links)

    return dict(grid=grid)


# crea una encuesta
def crea_encuesta():
    # solo crean encuestas los administradores
    # desde una conexión local
    if not (request.is_local and auth.has_membership(group_id='admin')):
        session.flash = 'Únicamente para administradores en local'
        redirect(URL('index'))

    form = SQLFORM(db.encuestas).process()

    if form.accepted:
        session.flash = 'Encuesta creada correctamente'
        redirect(URL('edita_encuesta', args=form.vars.id))
        # encuestas/default/edita_encuesta/<id>

    return dict(form=form)


# edita una encuesta
# encuestas/default/edita_encuesta/<id>
def edita_encuesta():
    def inicializa_acumulados(form):
        form.vars.acumulados = [0] * len(request.vars.opciones)

    # solo modifican encuestas los administradores
    # desde una conexión local
    if not (request.is_local and auth.has_membership(group_id='admin')):
        session.flash = 'Únicamente para administradores en local'
        redirect(URL('index'))

    id_encuesta = request.args(0, cast=int)

    encuesta = db.encuestas(id_encuesta)

    if not encuesta:
        redirect(URL('index'))

    # si ya se ha respondido no se puede modificar
    if db(db.respuestas.encuesta == id_encuesta).select():
        session.flash = 'La encuesta ya no es editable'
        redirect(URL('index'))

    db.preguntas.encuesta.default = id_encuesta
    db.preguntas.encuesta.readable = False
    db.preguntas.encuesta.writable = False
    form = SQLFORM(db.preguntas).process(onvalidation=inicializa_acumulados)

    preguntas = db(db.preguntas.encuesta == id_encuesta).select()

    if form.accepted:
        response.flash = 'Pregunta creada correctamente'

    return dict(encuesta=encuesta, preguntas=preguntas, form=form)



# ---- API (example) -----
@auth.requires_login()
def api_get_user_email():
    if not request.env.request_method == 'GET': raise HTTP(403)
    return response.json({'status':'success', 'email':auth.user.email})

# ---- Smart Grid (example) -----
@auth.requires_membership('admin') # can only be accessed by members of admin groupd
def grid():
    response.view = 'generic.html' # use a generic view
    tablename = request.args(0)
    if not tablename in db.tables: raise HTTP(403)
    grid = SQLFORM.smartgrid(db[tablename], args=[tablename], deletable=False, editable=False)
    return dict(grid=grid)

# ---- Embedded wiki (example) ----
def wiki():
    auth.wikimenu() # add the wiki to the menu
    return auth.wiki() 

# ---- Action for login/register/etc (required for auth) -----
def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())

# ---- action to server uploaded static content (required) ---
@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)
