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
        print(x)
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

def corresponde(line, clase):
    busq = search(r'.[ ]{1,}', line)
    loc = line[busq.end():len(line)-1]
    memory = formaterMemory(loc)
    if 'IMM' in clase:
        if '#' in line:
            if memory != None and int(memory, 16) <= middle:
                return ['IMM', f'{memory.upper()}']
            else:
                return ['IMM', '', 1]
    if 'IND,X' in clase or 'IND,Y' in clase:
        if ',y' in loc:
            if memory != None and int(memory, 16) <= maxim:
                return ['IND,Y', f'{memory.upper()}']
            else:
                return ['IND,Y', '', 1]
        elif ',x' in loc:
            if memory != None and int(memory, 16) <= maxim:
                return ['IND,X', f'{memory.upper()}']
            else:
                return ['IND,X', '', 1]
    if 'DIR' in clase or 'EXT' in clase:
        if memory != None and int(memory, 16) <= middle:
            return ['DIR', f'{memory.upper()}']
        elif memory != None and int(memory, 16) <= maxim:
            return ['EXT', f'{memory.upper()}']
        else:
            return ['EXT', '', 1]

    return None


def revision(line):
    # Minusculas
    line = line.lower()
    # Funcion anonima para transformar fila en operacion
    transform = lambda x: ints['Operación'][x]
    clase = []
    # Recorremos el conjunto de directivas
    for i in range(7):
        # Recorremos las operaciones en palabras
        for j in transform(ints_c[i][3]):
            # Verificamos si se puede separar en varias palabras
            if line.split(' '):
                # Si contiene la operacion se guarda el tipo de directiva
                if j == line.split(' ')[0]:
                    clase.append(direc[i])
            else:
                # Si contiene la operacion se guarda el tipo de directiva
                if j == line:
                    clase.append(direc[i])
    
    # En caso de tener mas de un tipo de directiva se revisa a cual
    # le corresponde
    if len(clase) > 1:
        clase = corresponde(line, clase)

    if len(clase) == 0:
        clase = ['Etiqueta']

    return clase

# Intenta abrir el archivo con codigo
with open('code.asm') as file:
    # Recorremos el codigo y lo separamos por linea
    code = [x for x in file if x != '\n']
    # Remplazamos los saltos de linea por vacio 
    code = list(map(lambda x : x.replace('\n', ''), code))
    # Arreglo de infomacion de cada linea
    info = []
    # Verificamos si se tiene el inicio y el fin
    if 'ORG' in code[0] and 'END' in code[len(code)-1]:
        # Recorremos todas las lineas de codigo
        for cont, i in enumerate(code):
            # Revisamos cada linea sacando su directiva
            if cont != 0 and cont != len(code)-1:
                info.append(revision(i))
        
        print(info)
    else:
        print('No tiene inicio o fin')