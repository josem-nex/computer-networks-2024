# Comandos RFC

## SYST

Método transfer_mode_info

## PASV

Método pasv_connect

## Response, send

Reciben y envían mensajes al servidor FTP.

## USER anonymous, PASS anonymous

Método default_login

## USER, PASS, ACCT

Método login

## HELP

Método help_ftp

## LIST

Método list_files

## CWD, CDUP

Método cwd

## PWD

Método pwd

## QUIT

Método close

## RMD

Método rm_dir

## MKD

Método mk_dir

## DELE

Método rm_file

## RNFR, RNTO

Método rename

## STOR

Método touch
Método stor
Método upload_file
Método upload_dir

## RETR

Método retr
Método download_file
Método download_dir

## SIZE

Método size

## REIN

Método rein
Método rein-local

## SMNT

Método smnt

## ABORT

Método abort
Método download_file

## NOOP

Método noop
Método idle

## PORT

Método portCnx

## TYPE

Método type

- A para ASCII
- I para binario

## STOU

Método store_unique

## APPE

Método append

## SITE

Método site_commands

## STAT

Método server_info

## NLST

Método nlst

## STRU

Método set_file_structure
F para archivo (sin estructura de registro)
R para estructura de registro
P para estructura de página

## MODE

Método set_transfer_mode
S para stream
B para block
C para compressed

## REST

Método restart_transfer
Solo funciona con el type I, binario
