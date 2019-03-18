

db.define_table(
    'encuestas',
    Field('nombre', 'string', requires=IS_NOT_EMPTY()),
    Field('descripcion', 'string'),
)

db.define_table(
    'preguntas',
    Field('encuesta', 'reference encuestas'),
    Field('enunciado', 'text', requires=IS_NOT_EMPTY()),
    Field('respuesta_text', 'list:string'),
    Field('respuesta_val', 'list:string'),
)

db.define_table(
    'respuestas',
    Field('encuesta', 'reference encuestas'),
    Field('IP', 'string', requires=IS_NOT_EMPTY()),
    Field('usuario', 'string')
)
