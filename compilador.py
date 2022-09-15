from pandas import read_excel as xls
from re import search

#Valores maximmos y minimos
middle = 255
maxim = 65535
# Extraccion de instrucciones
ints = xls('instrucciones.xls')
# Rellenamos espacios vacios
ints.fillna('#', inplace=True)
# Dividimos las directivas
direc = ['INH', 'IMM', 'DIR', 'EXT', 'IND,X', 'IND,Y', 'REL']
ints_c = []
inicio = 0
# Codigos de errores
error = {1 : 'out of memory'}
# Recorremos las directivas
for cont, i in enumerate(direc):
    # Separamos las directivas por tipo
    ints_c.append([x for x in ints.columns if i in x])
    # Encontramos las operaciones asociadas al tipo de directiva
    op = [x for x in ints.index if ints[ints_c[cont][0]][x] != '#']
    ints_c[cont].append(op)

def formaterMemory(x):
    # Caso hexadecimal
    if '$' in x:
        busq = search(r'\$[0-9a-f]{1,4}', x)
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
    loc = line[busq.end():len(line)-1]
    memory = formaterMemory(loc)
    if 'IMM' in clase:
        if '#' in line:
            if memory != None and int(memory, 16) <= middle:
                to_opcode(instruccion, 'IMM')
                return [instruccion, 'IMM', f'{memory.upper()}']
            else:
                return [instruccion, 'IMM', '', 1]
    if 'IND,X' in clase or 'IND,Y' in clase:
        if ',y' in loc:
            if memory != None and int(memory, 16) <= maxim:
                return [instruccion, 'IND,Y', f'{memory.upper()}']
            else:
                return [instruccion, 'IND,Y', '', 1]
        elif ',x' in loc:
            if memory != None and int(memory, 16) <= maxim:
                return [instruccion, 'IND,X', f'{memory.upper()}']
            else:
                return [instruccion, 'IND,X', '', 1]
    if 'DIR' in clase or 'EXT' in clase:
        if memory != None and int(memory, 16) <= middle:
            return [instruccion, 'DIR', f'{memory.upper()}']
        elif memory != None and int(memory, 16) <= maxim:
            return [instruccion, 'EXT', f'{memory.upper()}']
        else:
            return [instruccion, 'EXT', '', 1]

    return None

# Busca el opcode de la instruccion dada
def to_opcode(instruccion, directiva):
    row = ints[ints.Operación.str.contains(instruccion.lower(), na=False)]
    return row[f'OPCODE {directiva}'].values[0]

def revision(line):
    # Minusculas
    line = line.lower()
    # Funcion anonima para transformar fila en operacion
    transform = lambda x: ints['Operación'][x]
    clase = []
    if search(r'$[ ]{1,}', line) == None:
        # Instruccion dada
        instruccion = ''
        # Recorremos el conjunto de directivas
        for i in range(len(direc)):
            # Recorremos las operaciones en palabras
            for j in transform(ints_c[i][3]):
                # Verificamos si se puede separar en varias palabras
                if line.split(' '):
                    # Si contiene la operacion se guarda el tipo de directiva
                    if j == line.split(' ')[0]:
                        clase.append(direc[i])
                        instruccion = j
                else:
                    # Si contiene la operacion se guarda el tipo de directiva
                    if j == line:
                        clase.append(direc[i])
                        instruccion = j
        
    # En caso de tener mas de un tipo de directiva se revisa a cual
    # le corresponde
    if len(clase) > 1:
        clase = corresponde(instruccion.upper(), line, clase)
        clase[0] = to_opcode(clase[0], clase[1])
    elif len(clase) == 0:
        clase = [line.upper(), 'Etiqueta']
    elif len(clase) == 1:
        clase = [to_opcode(instruccion, clase[0]), clase[0]]

    return clase

def s19():
    # genera el arhivo s19
    with open('./code.s19', 'w') as file:
        file.write(f'<{inicio}> ')
        cont = 0
        nex_pos = inicio
        for i in info:
            if i[2] != 'Etiqueta':
                if type(i[1]) == str and len(i[1]) == 3:
                    l = i[1].replace(' ', '')
                    file.write(f'{l} ')
                    cont += 1
                elif type(i[1]) == str and len(i[1]) == 5:
                    if cont+2 > 16:
                        high = i[1].split(' ')[0]
                        file.write(f'{high} ')
                        nex_pos = hex(int(nex_pos, 16)+16)
                        file.write(f'\n<{nex_pos[2:]}> ')
                        cont = 0
                        low = i[1].split(' ')[1]
                        file.write(f'{low} ')
                        cont += 1
                    else:
                        file.write(f'{i[1]} ')
                        cont += 2
                else:
                    file.write(f'{i[1]} ')
                    cont += 1
                if cont == 16:
                    nex_pos = hex(int(nex_pos, 16)+16)
                    file.write(f'\n<{nex_pos[2:]}> ')
                    cont = 0

# Intenta abrir el archivo con codigo
with open('code.asm') as file:
    # Recorremos el codigo y lo separamos por linea
    code = [x for x in file if x != '\n']
    # Remplazamos los saltos de linea por vacio 
    code = list(map(lambda x : x.replace('\n', ''), code))
    # Arreglo de infomacion de cada linea
    info = []
    # Recorremos todas las lineas de codigo
    for cont, i in enumerate(code):
        # Salimos del recorrido si se encuentra el termino del codigo
        if 'END' in i:
            break
        elif 'ORG' in i:
            busq = search(r'\$[0-9]{1,4}', i)
            inicio = i[busq.start()+1:busq.end()]
            pass
        # Salta comentario de linea
        elif search(r'^\*.', i) != None:
            pass
        else:
            temp = revision(i)
            temp.insert(0, cont)
            # Revisamos cada linea sacando su directiva
            info.append(temp)
    
    s19()