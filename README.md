# Hollowman

The thought of human invisibility has intrigued man for centuries. Highly gifted scientist Sebastian Caine develops a serum that induces complete invisibility. His remarkable transformation results in unimaginable power that seems to suffocate his sense of morality and leads to a furious and frightening conclusion.

## Changelog

* 0.0.29
  - Migração para python 3.6

* 0.0.28
  - Atualizando example-plugin. Corrigindo chamada à Dialog API.

* 0.0.27
  - Atualizando immage base para uwsgi/py27:0.0.12 (Log "JSON")

* 0.0.26
  - Adicionado lógica para dupla autenticação: Token JWT (com oauth2) e Token de usuário
  - Adicionadas novas configurações: HOLLOWMAN_DB_ECHO, HOLLOWMAN_ENFORCE_AUTH, HOLLOWMAN_DB_URL

* 0.0.25
  - Adicionadas rotas pra servir o código dos plugins para a UI
  - Atualização para imagem base alpine/py27/uwsgi20:0.0.11, por causa do `UWSGI_EXTRA_ARGS`
  - Necessidade de passar `UWSGI_EXTRA_ARGS="--static-map2 /static=/opt/app/"`
  - Adição de um plugin de exemplo
* 0.0.24
  - Migrando para Flask-OAuthlib
* 0.0.23
  - Adicionado todo o fluxo para autenticação oauth2, mas ainda não é obrigatório. 

## Env vars
* MARATHON_CREDENTIALS [required] user:pass for the basic auth
* MARATHON_ENDPOINT [required] Where to connect to find marathon api
* HOLLOWMAN_REDIRECT_ROOTPATH_TO: Env que diz para onde o usuario será redirecionado se acessar a raiz onde o hollowman está deployado. Defaults to `/v2/apps`
* HOLLOWMAN_GOOGLE_OAUTH2_CLIENT_ID: ID da app Oauth2, registrado no console do Google
* HOLLOWMAN_GOOGLE_OAUTH2_CLIENT_SECRET: Secret dessa app.
* HOLLOWMAN_SECRET_KEY: Secret usado pelo Flask
* HOLLOWMAN_REDIRECT_AFTER_LOGIN: URL pra onde o usuário será redirecionado após o fluxo do oauth2. O redirect é feito pra: `URL?jwt=<token_jwt>`
* HOLLOWMAN_DB_ECHO: Define se os logs do SQLAlchemy estão ligados: Valores possíveis: 1|0. Default 0
* HOLLOWMAN_ENFORCE_AUTH: Define se o códifo vai exigir autenticaçáo em todos os requests. Valores possíveis: 1|0. Default 0
* HOLLOWMAN_DB_URL: URL completa (com user, pwd, host, schema) do banco de dados: Formato: `postgresql://<user>:<pwd>@<host>/<schema>`


## Opções específicas de filtros

Qualquer filtro pode ser desliagdo por app caso a app possua a label `hollowman.filter.<name>.disable=<anyvalue>`. Onde `<name>` é o 
valor do atributo `name` da classe que implementa o filtro em questão.


Um filtro qualquer pode ser desabilitado **globalmente** usando a envvar: HOLLOWMAN_FILTER_<NAME>_DISABLE: "qualquer-valor". 


A ausência da env ou da label significa que o filtro está ligado.

### Passando parametros adcionais para um filtro

É possível passar parametros abritrários para um filtro qualquer via envvar. O nome da env deve ser:

`HOLLOWMAN_FILTER_<FILTER>_PARAM_<OPTIONNAME>_<INDEX>` onde:

`<FILTER>` é o nome do filtro
`<OPTIONNAME>` e o nome do parametro
`<INDEX>` é um indice para quando precisamos passar uma lista



## Parametros por Filtro

### Constraint

O Filtro DNS recebe o parametro `BASECONSTRAINT`. Esse parametro diz quais constraints serão adicionadas a uma pp caso ela não tenha nenhuma. Isso significa que o nome da env é: `HOLLOWMAN_FILTER_CONSTRAINT_PARAM_BASECONSTRAINT_{0,1,2}`


## Como adicionar novos plugins para a UI


Para adicionar novos plugins o `main.js` do plugin deve ser comitado em `/static/plugins/<plugin-id>/main.js`
Alteramos o arquivo `app.py` e adicionamos uma nova chamada a `register_plugin(<plugin-id>)`

Isso é o mínimo neceessário para que esse novo plugin esteja disponível para a UI.




## Running tests
`py.test --cov=hollowman --cov-report term-missing -v -s`
