from math import inf
from pandas import read_excel as xls
from re import search
from numpy import where

#Valores maximmos y minimos
middle = 255
maxim = 65535
# Extraccion de instrucciones
ints = xls('instrucciones.xls')
# Dividimos las directivas
direc = ['INH', 'IMM', 'DIR', 'EXT', 'IND,X', 'IND,Y', 'REL']
inicio = 0
# Codigos de errores
error = {'4' : 'MNEMÓNICO INEXISTENTE',
        '7' : 'MAGNITUD DE OPERANDO ERRONEA', 
        '9' : 'INSTRUCCIÓN CARECE DE AL MENOS UN ESPACIO RELATIVO AL MARGEN',
        '10' : 'NO SE ENCUENTRA END'}

def formaterMemory(x):
    # Caso hexadecimal
    if '$' in x:
        busq = search(r'\$[0-9a-f]{1,}', x)
        if busq != None:
            return x[busq.start()+1:busq.end()]
        else:
            return None
    # Caso de numero ascii
    elif '\'' in x:
        busq = search(r'\'[0-9a-f]{1}', x)
        if busq != None:
            pass
        else:
            return None
    # Caso de numero decimal
    else:
        busq = search(rf'.[0-9]{maxim}', x)
        if busq != None:
            return hex(x[busq.start()+1:busq.end()])
        else:
            return None

def corresponde(instruccion, line, clase):
    busq = search(r'.[ ]{1,}', line)
    loc = line[busq.end():len(line)]
    memory = formaterMemory(loc)
    if 'IMM' in clase:
        if '#' in line:
            if memory != None and int(memory, 16) <= middle:
                to_opcode(instruccion, 'IMM')
                return [instruccion, 'IMM', f'{memory.upper()}']
            else:
                return [instruccion, 'ERROR', 7]
    if 'IND,X' in clase or 'IND,Y' in clase:
        if ',y' in loc:
            if memory != None and int(memory, 16) <= maxim:
                return [instruccion, 'IND,Y', f'{memory.upper()}']
            else:
                return [instruccion, 'ERROR', 7]
        elif ',x' in loc:
            if memory != None and int(memory, 16) <= maxim:
                return [instruccion, 'IND,X', f'{memory.upper()}']
            else:
                return [instruccion, 'ERROR', 7]
    if 'DIR' in clase or 'EXT' in clase:
        if memory != None and int(memory, 16) <= middle:
            return [instruccion, 'DIR', f'{memory.upper()}']
        elif memory != None and int(memory, 16) <= maxim:
            return [instruccion, 'EXT', f'{memory.upper()}']
        else:
            return [instruccion, 'ERROR', 7]

    return None

# Busca el opcode de la instruccion dada
def to_opcode(instruccion, directiva):
    row = ints[ints.Operación.str.contains(instruccion, na=False)]
    return row[f'OPCODE {directiva}'].values[0]

def revision(line):
    # Minusculas
    line = line.lower()
    # Funcion anonima para transformar fila en operacion
    # transform = lambda x: ints['Operación'][x]
    clase = []
    # Si esta identado lo considera instruccion 
    if search(r'^[ ]+', line) != None:
        # Elimina los espacios previos a la instruccion
        recorte = search(r'^[ ]+', line)
        line = line[recorte.end():]
        # Instruccion dada
        instruccion = ''
        # Separa en partes la linea
        if line.split(' '):
            # La primer palabra debe ser la instruccion
            instruccion = line.split()[0]
            # Busca la instruccion en la lista de instrucciones
            row = ints[ints.Operación.str.contains(instruccion, na=False)]
            # Elimina columnas vacios
            row = row.dropna(axis=1)
            # Revisa si encontro coicidencias
            if row.empty == False:
                # Encuentra los indices de los metodos de direccionamiento
                # que conciden con la instruccion
                index = where(row.columns.str.contains(f'OPCODE {direc}') == True)
                # Si es mayor a uno agrega todos los metodos
                if len(index[0]) > 1:
                    for i in index[0]:
                        clase.append(row.columns[i].split(' ')[1])
                # Sino agrega solo el metodo
                else:
                    clase.append(row.columns[index[0][0]].split(' ')[1])
            else:
                return [instruccion, 'ERROR', 4]
    else:
        # La primer palabra debe ser la instruccion
        instruccion = line.split()[0]
        # Busca la instruccion en la lista de instrucciones
        row = ints[ints.Operación.str.contains(instruccion, na=False)]
        # Elimina columnas vacios
        row = row.dropna(axis=1)
        # Revisa si encontro coicidencias
        if not row.empty:
            return [instruccion, 'ERROR', 9]
    # En caso de tener mas de un tipo de directiva se revisa a cual
    # le corresponde
    if len(clase) > 1:
        clase = corresponde(instruccion, line, clase)
        if clase[1] != 'ERROR':
            clase[0] = to_opcode(clase[0], clase[1])
    elif len(clase) == 0:
        clase = [line.upper(), 'Etiqueta']
    elif len(clase) == 1:
        clase = [to_opcode(instruccion, clase[0]), clase[0]]

    return clase

def divisionHexa(file, cont, i, nex_pos, idx):
    if cont+2 > 16:
        # Escritura de parte alta del hexa
        high = i[idx].split(' ')[0]
        file.write(f'{high} ')
        nex_pos = hex(int(nex_pos, 16)+16)
        # Escritura de nueva posicion del hexa
        file.write(f'\n<{nex_pos[2:]}> ')
        cont = 0
        low = i[idx].split(' ')[1]
        # Escritura de parte baja del hexa
        file.write(f'{low} ')
        cont += 1
    # Se colocan los dos hexa
    else:
        file.write(f'{i[idx]} ')
        cont += 2
    
    return cont, nex_pos

def s19():
    # genera el arhivo s19
    with open('./code.s19', 'w') as file:
        # Escribimos el lugar en memoria donde inicia el programa
        file.write(f'<{inicio}> ')
        cont = 0
        nex_pos = inicio
        info2 = [x for x in info if x != '']
        cont2 = len(info2)
        # Recorremos el arreglo de operaciones
        for i in info:
            try:
            # Si es una etiqueta la saltamos
                if len(i) > 1 and i[2] != 'Etiqueta':
                    # Si tiene tamaño 3 significa que tiene un espacio
                    # y es un numero hexa de dos caracteres
                    if type(i[1]) == str and len(i[1]) == 3:
                        l = i[1].replace(' ', '')
                        file.write(f'{l} ')
                        cont += 1
                    # Si tiene tamaño 5 significa que tiene un espacio
                    # y es dos numeros hexa de dos caracteres
                    elif type(i[1]) == str and len(i[1]) == 5:
                        # Si se pasa de los 16 bits al colocar dos hexa
                        # se hace un salto de linea (uno y uno)
                        cont, nex_pos = divisionHexa(file, cont, i, nex_pos, 1)
                    # No tiene espacios entonces se puede escribir
                    else:
                        file.write(f'{i[1]} ')
                        cont += 1
                    # Seccion que coloca los valores hexadecimales
                    # de las instrucciones
                    if len(i) > 3:
                        # Si el tamaño del valor es 4 se colocan los dos valores
                        if len(i[3]) == 4:
                            i[3] = f'{i[3][0:2]} {i[3][2:]}'
                            cont, nex_pos = divisionHexa(file, cont, i, nex_pos, 3)
                        # Si el tamaño del valor es 1 se agrega un cero al inicio 
                        elif len(i[3]) == 1:
                            file.write(f'0{i[3]} ')
                            cont += 1
                        # Si el tamaño del valor es 3 se agrega un cero al inicio 
                        elif len(i[3]) == 3:
                            i[3] = f'0{i[3][1]} {i[3][2:]}'
                            cont, nex_pos = divisionHexa(file, cont, i, nex_pos, 3)
                        # No tiene espacios entonces se puede escribir
                        else:
                            file.write(f'{i[3]} ')
                            cont += 1
                    # Si ya se escribieron 16 caracteres se
                    # hace un salto de linea con la nueva posicion en memoria
                    # pero solo si todavia existen lineas analizables
                    if cont == 16 and cont2-1 > 0:
                        nex_pos = hex(int(nex_pos, 16)+16)
                        file.write(f'\n<{nex_pos[2:]}> ')
                        cont = 0
                cont2 -= 1
            except:
                pass

# Intenta abrir el archivo con codigo
with open('code.asm') as file:
    # Bandera para saber si existen errores
    errores = False
    # Bandera para saber si hay final
    end = False
    # Arreglo de data
    info = []
    # Recorremos todas las lineas de codigo
    for cont, i in enumerate(file):
        # Salimos del recorrido si se encuentra el termino del codigo
        if 'END' in i:
            end = True
            info.append('')
            break
        # Salta ORG
        elif 'ORG' in i:
            busq = search(r'\$[0-9]{1,4}', i)
            inicio = i[busq.start()+1:busq.end()]
            info.append('')
        # Salta comentario de linea
        elif search(r'^\*.', i) != None:
            info.append('')
        # Salta salto de linea
        elif search(r'^\n$', i):
            info.append('')
        # Encontramos los datos relevantes de las
        # instrucciones
        else:
            temp = revision(i)
            temp.insert(0, cont)
            if len(temp) > 2 and temp[2] == 'ERROR':
                errores = True
            info.append(temp)
    # Encontramos error por falta de END
    if end == False:
        info.append(['ERROR', 10])
# Se verifica si hay errores
if errores:
    # Se crea un archivo especial para marcar los errores
        with open('code.lst', 'w') as correct:
        # Se vuelve a recorrer el archivo inicial
            with open('code.asm') as file:
                for cont, i in enumerate(file):
                # Se escribe el mismo codigo
                    correct.write(f'{i}')
                    # Se escribe el mismo codigo
                    if 'ERROR' in info[cont]:
                        correct.write(f'{error[str(info[cont][3])]}\n')
else:
    s19()