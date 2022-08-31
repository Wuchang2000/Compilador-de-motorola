from pandas import read_excel as xls
from re import search

# Extraccion de instrucciones
ints = xls('instrucciones.xls')
# Rellenamos espacios vacios
ints.fillna('#', inplace=True)
# Dividimos las directivas
direc = ['INH', 'IMM', 'DIR', 'EXT', 'IND,X', 'IND,Y', 'REL']
ints_c = []
# Recorremos las directivas
for cont, i in enumerate(direc):
    # Separamos las directivas por tipo
    ints_c.append([x for x in ints.columns if i in x])
    # Encontramos las operaciones asociadas al tipo de directiva
    op = [x for x in ints.index if ints[ints_c[cont][0]][x] != '#']
    ints_c[cont].append(op)

def corresponde(line, clase):
    if 'IMM' in clase:
        if '#' in line:
            return ['IMM']
    if 'IND,X' in clase or 'IND,Y' in clase:
        if ',y' in line.split(' ')[1]:
            return ['IND,Y']
        elif ',x' in line.split(' ')[1]:
            return ['IND,X']
    if 'DIR' in clase:
        loc = line.split()[1]
        if '$' in loc:
            loc = loc.replace('$', '')
        if len(loc) < 4:
            loc = ((4-len(loc))*'0')+loc
        if search(r'^00([0-9a-f]{2})$', loc) != None:
            return ['DIR']

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

    print(clase)

    return True

# Intenta abrir el archivo con codigo
with open('code.asm') as file:
    # Recorremos el codigo y lo separamos por linea
    code = [x for x in file if x != '\n']
    # Remplazamos los saltos de linea por vacio 
    code = list(map(lambda x : x.replace('\n', ''), code))
    # Verificamos si se tiene el inicio y el fin
    if 'ORG' in code[0] and 'END' in code[len(code)-1]:
        # Recorremos todas las lineas de codigo
        for cont, i in enumerate(code):
            # Revisamos cada linea sacando su directiva
            if cont != 0 and cont != len(code)-1 \
                and revision(i) == False:
                print('Hay un error')
    else:
        print('No tiene inicio o fin')