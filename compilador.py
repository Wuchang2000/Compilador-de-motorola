from random import randint
from pandas import read_excel as xls
from re import search, compile
from numpy import where, array
import argparse as arg
from os import path

#Valores maximmos y minimos
middle = 255
maxim = 65535
# Extraccion de instrucciones
ints = xls('instrucciones.xls')
# Dividimos las directivas
direc = ['INH', 'IMM', 'DIR', 'EXT', 'IND,X', 'IND,Y', 'REL']
inst_tres = ['brclr', 'brset']
inst_dos = ['bclr', 'bset']
etiquetas = []
inicio = ''
inicios = []
style = """<style type='text/css'>
html {
    font-family: Arial;
    font-size: 16px;
}
r {
    color: #ff0000;
}
b {
    color: #0000ff;
}
</style>"""
# Codigos de errores
error = {'1' : 'CONSTANTE INEXISTENTE',
        '2' : 'VARIABLE INEXISTENTE',
        '3' : 'ETIQUETA INEXISTENTE',
        '4' : 'MNEMÓNICO INEXISTENTE',
        '5' : 'INSTRUCCIÓN CARECE DE OPERANDOS',
        '6' : 'INSTRUCCIÓN NO LLEVA OPERANDO(S)',
        '7' : 'MAGNITUD DE OPERANDO ERRONEA',
        '8' : 'SALTO RELATIVO MUY LEJANO',
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
            return hex(x[busq.start()+1:busq.end()])
        else:
            return None
    # Caso de numero decimal
    else:
        busq = search(rf'.[0-9]{maxim}', x)
        if busq != None:
            return hex(x[busq.start()+1:busq.end()])
        else:
            return None

# Quita espacios inecesarios en las lineas de codigo
def formatoLinea(line):
    newLine = []
    if len(line.split(' ')) > 3:
        for i in line.split(' '):
            if i:
                newLine.append(i)
    else:
        newLine = line.split(' ')

    return newLine

# Sustituye variables y constantes en sus valores
def susValue(file):
    # Recorremos el codigo y le quitamos simbolos inservibles
    file = array([x[1].lower().replace('\n', '') for x in enumerate(file)])
    # Recorremos el codigo para sustituir el
    # valor de la constante/variable
    for cont, i in enumerate(file):
        # Si esta la instruccion EQU significa que existe
        # una constante/variable
        if 'equ' in i and search(r'^\*.*equ', i) == None:
            # Conseguimos el nombre de la constante/variable
            # y su valor
            pseudo = formatoLinea(i)[0]
            value = formatoLinea(i)[2].replace('\n', '')
            # Recorremos el arreglo para sustituir por el valor
            for cont1, j in enumerate(file):
                if len(list(filter(compile(r'[#,]{0,1}%s$' % pseudo).match, j.split(' ')))) > 0\
                and 'equ' not in j:
                    if 'clr' not in j:
                        if search(r'\$[0]{2}', value) != None:
                            recorte = search(r'\$[0]{2}', value)
                            t = value[0:recorte.start()+1] + value[recorte.end():]
                            file[cont1] = j.replace(pseudo, t)
                        else:
                            file[cont1] = j.replace(pseudo, value)
                    else:
                        file[cont1] = j.replace(pseudo, value)
            # Quitamos la linea con la variable para evitar ruido
            # en analisis posterior
            file[cont] = ''
        elif i != '' and search(r'^[^* ]{1,}[ ]*', i) != None:
            etiquetas.append(i.split(' ')[0])

    # Retornamos el codigo modificado
    return file

# Funcion que encuentra la directiva a la que corresponde
def corresponde(instruccion, line, clase):
    doble = False
    triple = False
    memory1 = ''
    memory2 = ''
    # Si aparece la instriccion con dos operandos
    if instruccion in inst_dos:
        # Quitamos los espacios del inicio de la instruccion
        busq = search(r'.[ ]{1,}.', line)
        if busq != None:
            loc = line[busq.end()-1:len(line)]
            # Extraemos el valor del operando
            memory = formaterMemory(loc)
            busq1 = search(r'#[$].{1,4}', loc)
            if busq1 != None:
                memory1 = formaterMemory(loc[busq1.start():])
                if memory1 != None and int(memory, 16) <= maxim:
                    doble = True
                else:
                    # Error por magnitud erronea
                    return [instruccion, 'ERROR', 7]
            else:
                # Error por magnitud erronea
                return [instruccion, 'ERROR', 7]
    # Si aparece la instruccion con tres operandos
    if instruccion in inst_tres:
        # Quitamos los espacios del inicio de la instruccion
        busq = search(r'.[ ]{1,}.', line)
        if busq != None:
            loc = line[busq.end()-1:len(line)]
            # Extraemos el valor del operando
            memory = formaterMemory(loc)
            busq1 = search(r'#[$].{1,4}', loc)
            if busq1 != None:
                memory1 = formaterMemory(loc[busq1.start():])
                if memory1 != None and int(memory, 16) <= maxim:
                    busq2 = search(r' [a-z0-9]{1,}', loc)
                    if busq2 != None and loc[busq2.start()+1:].replace(' ', '') in etiquetas:
                        memory2 = loc[busq2.start()+1:].replace(' ', '')
                        triple = True
                    else:
                        return [instruccion, 'ERROR', 3]
                else:
                    # Error por magnitud erronea
                    return [instruccion, 'ERROR', 7]
            else:
                # Error por magnitud erronea
                return [instruccion, 'ERROR', 7]
    if True:
        # Quitamos los espacios del inicio de la instruccion
        busq = search(r'.[ ]{1,}.', line)
        if busq != None:
            loc = line[busq.end()-1:len(line)]
            if loc in etiquetas and 'REL' not in clase:
                return [instruccion, clase, loc]
            # Extraemos el valor del operando
            memory = formaterMemory(loc)
    # Subrutinas
    if 'FCB' in clase:
        # Quitamos los espacios del inicio de la instruccion
        busq = search(r'.[ ]{1,}.', line)
        if busq != None:
            loc = line[busq.end()-1:len(line)]
            # Extraemos el valor del operando
            memory = formaterMemory(loc)
            busq1 = search(r',[$].{1,4}', loc)
            if busq1 != None:
                memory1 = formaterMemory(loc[busq1.start()+1:])
                if memory1 != None and int(memory, 16) <= middle:
                    return [subrun.upper(), 'FCB', f'{memory.upper()+memory1.upper()}']
                else:
                    # Error por magnitud erronea
                    return [instruccion, 'ERROR', 7]
            else:
                # Error por magnitud erronea
                return [instruccion, 'ERROR', 7]
    # Metodo de direccionamiento inherente
    if 'INH' in clase:
        if busq != None:
            # Error no lleva operando
            return [instruccion, 'ERROR', 6]
        else:
            return [instruccion, 'INH']
    if 'REL' in clase:
        # Error por no llevar operandos
        if busq == None:
            return [instruccion, 'ERROR', 5]
        # Error por etiqueta inexistente
        elif loc.replace(' ', '') not in etiquetas:
            return [instruccion, 'ERROR', 3]
        else:
            if memory == None:
                etiq = search(r' [a-z1-9]{1,}', line)
                return [instruccion, 'REL', line[etiq.start()+1:]]
    # Metodo de direccionamiento inmediato
    if 'IMM' in clase:
        if '#' in line:
            # Error por no llevar operandos
            if busq == None:
                return [instruccion, 'ERROR', 5]
            elif memory != None and int(memory, 16) <= maxim:
                to_opcode(instruccion, 'IMM')
                return [instruccion, 'IMM', f'{memory.upper()}']
            # Error por constante inexistente
            elif memory == None:
                return [instruccion, 'ERROR', 1]
            # Error por magnitud erronea
            else:
                return [instruccion, 'ERROR', 7]
    # Metodo de direccionamiento indexado
    if 'IND,X' in clase or 'IND,Y' in clase:
        # Error por no llevar operandos
        if busq == None:
            return [instruccion, 'ERROR', 5]
        elif ',y' in loc:
            if memory != None and int(memory, 16) <= maxim:
                if doble:
                    return [instruccion, 'IND,Y', f'{memory.upper()+memory1.upper()}']
                if triple:
                    return [instruccion, 'IND,Y', f'{memory.upper()+memory1.upper()+memory2}']
                else:
                    return [instruccion, 'IND,Y', f'{memory.upper()}']
            # Error por variable inexistente
            elif memory == None:
                return [instruccion, 'ERROR', 2]
            # Error por magnitud erronea
            else:
                return [instruccion, 'ERROR', 7]
        elif ',x' in loc:
            if memory != None and int(memory, 16) <= maxim:
                if doble:
                    return [instruccion, 'IND,X', f'{memory.upper()+memory1.upper()}']
                if triple:
                    return [instruccion, 'IND,X', f'{memory.upper()+memory1.upper()+memory2}']
                else:
                    return [instruccion, 'IND,X', f'{memory.upper()}']
            # Error por variable inexistente
            elif memory == None:
                return [instruccion, 'ERROR', 2]
            # Error por magnitud erronea
            else:
                return [instruccion, 'ERROR', 7]
    # Metodo de direccionamiento directo y extendido
    if 'DIR' in clase or 'EXT' in clase:
        # Error por no llevar operandos
        if busq == None:
            return [instruccion, 'ERROR', 5]
        # Comparacion de intervalo de hexa
        elif memory != None and int(memory, 16) <= middle \
            and 'DIR' in clase:
            if doble:
                return [instruccion, 'DIR', f'{memory.upper()+memory1.upper()}']
            if triple:
                return [instruccion, 'DIR', f'{memory.upper()+memory1.upper()+memory2}']
            else:
                return [instruccion, 'DIR', f'{memory.upper()}']
        elif memory != None and int(memory, 16) <= maxim \
            and 'EXT' in clase:
            return [instruccion, 'EXT', f'{memory.upper()}']
        # Error por variable inexistente
        elif memory == None:
            return [instruccion, 'ERROR', 2]
        # Error por magnitud erronea
        else:
            return [instruccion, 'ERROR', 7]

    return None

# Busca el opcode de la instruccion dada
def to_opcode(instruccion, directiva):
    row = ints[ints.Operación.str.contains(r'^%s$' % instruccion, na=False)]
    return row[f'OPCODE {directiva}'].values[0]

# Busca la directiva, trata varias directivas asociada a la intruccion
# encuentra etiquetas
def revision(line):
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
            row = ints[ints.Operación.str.contains(r'^%s$' % instruccion, na=False)]
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
            elif 'fcb' in line:
                clase.append('FCB')
            else:
                # No existe la instruccion
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
    if len(clase) >= 1:
        clase = corresponde(instruccion, line, clase)
        if clase[1] != 'ERROR' and clase[1] in direc:
            clase[0] = to_opcode(clase[0], clase[1])
    elif len(clase) == 0:
        clase = [line.split(' ')[0].replace(' ', ''), 'Etiqueta']

    return clase

# Creamos archivo lst
def Lst():
    # Abrimos el archivo original
    with open(args.f) as file1:
        # Quitamos los saltos de linea para controlar
        # el formato
        file1 = [x.replace('\n', '') for x in file1]
        # Creamos el archivo lst
        with open(f'./{args.f}-lst.html', 'w') as lst:
            lst.write('<html>')
            lst.write(style)
            # Recorremos las lineas de codigo
            for x, i in enumerate(file1):
                # Checamos que se tenga una instruccion
                if info[x] != '' and not 'Etiqueta' in info[x]:
                    # Escribimos en el archivo la linea con formato
                    data = f'{codigo[x][0]}: {codigo[x][1]} <r>{codigo[x][3]}</r><b>{codigo[x][4]}</b>'\
                        .ljust(34, ' ')
                    lst.write(f'<p><pre>{data}:{i}</pre></p>\n')
                # Si es la ultima linea evitamos un salto de linea
                elif x == len(file1)-1:
                    a = f'{x}: Vacio'.ljust(20, ' ')
                    lst.write(f'<p><pre>{a}:{i}</pre></p>')
                # Escribimos las lineas que no tengan instruccuiones calculadas
                else:
                    a = f'{x}: Vacio'.ljust(20, ' ')
                    lst.write(f'<p><pre>{a}:{i}</pre></p>\n')
            lst.write('</html>')


def verificaLinea(idx):
    existe = False
    for i in range(idx, len(codigo)):
        if codigo[i] != '' and not 'ORG' in codigo[i]\
            and not 'Etiqueta' in codigo[i]:
            existe = True
    return existe

def s19():
    # genera el arhivo s19
    with open(f'./{args.f}-s19.html', 'w') as S19:
        # Escribimos el lugar en memoria donde inicia el programa
        data = ''
        cont = 0
        next_pos = inicio
        S19.write('<html>')
        S19.write(style)
        S19.write('<p><pre>')
        data += f'&lt{inicio}&gt '
        # Recorremos el arreglo de operaciones
        for y, i in enumerate(codigo):
            if i != '' and i[2] != 'Etiqueta':
                if i[3] != '':
                    if len(i[3]) > 2:
                        meirei = [i[3][x:x+2] for x in range(0, len(i[3]), 2)]
                        if cont+len(meirei) > 16:
                            next_pos = hex(int(next_pos, 16)+int('10', 16))[2:]
                            difer = abs(cont - 16)
                            data += f'<r>{" ".join(meirei[:difer])}</r>'+\
                                f'\n&lt{next_pos.upper()}&gt '+\
                                    f'<r>{" ".join(meirei[difer:])}</r> '
                            cont = len(meirei[difer:])
                        elif cont+len(meirei) == 16:
                            next_pos = hex(int(next_pos, 16)+int('10', 16))[2:]
                            if verificaLinea(y):
                                data += f'<r>{" ".join(meirei)}</r>'+\
                                    f'\n&lt{next_pos.upper()}&gt '
                            else:
                                data += f'<r>{" ".join(meirei)} </r>'
                            cont = 0
                        else:
                            data += f'<r>{" ".join(meirei)} </r>'
                            cont += len(meirei)
                    else:
                        meirei = i[3]
                        if cont+1 > 16:
                            next_pos = hex(int(next_pos, 16)+int('10', 16))[2:]
                            data += f'\n&lt{next_pos.upper()}&gt {meirei} '
                            cont = 1
                        elif cont+1 == 16:
                            next_pos = hex(int(next_pos, 16)+int('10', 16))[2:]
                            if verificaLinea(y):
                                data += f'<r>{meirei}</r>\n&lt{next_pos.upper()}&gt '
                            else:
                                data += f'<r>{meirei} </r>'
                            cont = 0
                        else:
                            data += f'<r>{meirei} </r>'
                            cont += 1
                if i[4] != '':
                    if len(i[4]) > 2:
                        oper = [i[4][x:x+2] for x in range(0, len(i[4]), 2)]
                        if cont+len(oper) > 16:
                            next_pos = hex(int(next_pos, 16)+int('10', 16))[2:]
                            difer = abs(cont - 16)
                            data += f'<b>{" ".join(oper[:difer])}</b>'+\
                                f'\n&lt{next_pos.upper()}&gt <b>{" ".join(oper[difer:])}</b> '
                            cont = len(oper[difer:])
                        elif cont+len(oper) == 16:
                            next_pos = hex(int(next_pos, 16)+int('10', 16))[2:]
                            if verificaLinea(y):
                                data += f'<b>{" ".join(oper)}</b>'+\
                                    f'\n&lt{next_pos.upper()}&gt '
                            else:
                                data += f'<b>{" ".join(oper)}</b> '
                            cont = 0
                        else:
                            data += f'<b>{" ".join(oper)} </b>'
                            cont += len(oper)
                    else:
                        oper = i[4]
                        if cont+1 > 16:
                            next_pos = hex(int(next_pos, 16)+int('10', 16))[2:]
                            data += f'\n&lt{next_pos.upper()}&gt <b>{oper} </b>'
                            cont = 1
                        elif cont+1 == 16:
                            next_pos = hex(int(next_pos, 16)+int('10', 16))[2:]
                            if verificaLinea(y):
                                data += f'<b>{oper}</b>\n&lt{next_pos.upper()}&gt '
                            else:
                                data += f'<b>{oper} </b>'
                            cont = 0
                        else:
                            data += f'<b>{oper} </b>'
                            cont += 1
            elif len([x for x in inicios if x[0] == y]) == 1:
                next_pos = [x for x in inicios if x[0] == y][0][2].upper()
                cont = 0
                data += f'\n&lt{next_pos.upper()}&gt '

        S19.write(data)
        S19.write('</pre></p>')
        S19.write('</html>')
    
    with open(f'./{args.f}-s19-Motorola.html', 'w') as Moto: 
        motorola = []
        data1 = data.split('\n')
        for x in data1:
            temp = x.replace('<r>', '')\
                .replace('</r>', '').replace('&gt', '')\
                    .replace('<b>', '').replace(' ', '')\
                        .replace('</b>', '').replace('&lt', '')
            checksum = hex(randint(0, 255))[2:].upper()
            if len(checksum) < 2:
                cont = '0'+cont
            cont = hex(int((len(temp)+2)/2))[2:].upper()
            if len(cont) < 2:
                cont = '0'+cont
            motorola.append(f'S1{cont}'+x.replace(' ', '')\
                .replace('&gt', '').replace('&lt', '')+checksum)

        Moto.write('<html>')
        Moto.write(style)
        Moto.write('<p><pre>')
        for x in motorola:
            Moto.write(x+'\n')
        checksum = hex(randint(0, 255))[2:].upper()
        if len(checksum) < 2:
            cont = '0'+cont
        Moto.write(f'S9030000{checksum}')
        Moto.write('</pre></p>')
        Moto.write('</html>')

def posicionMemory(i):
    cont = 0
    instruc = ''
    operando = ''
    operando1 = ''
    # Se agrega el valor de la instruccion
    instruc = str(i[1]).replace(' ', '')
    if len(instruc) > 2:
        cont += 2
    else:
        cont += 1
    # Se almacena el valor del operando con formato
    if len(i) > 3:
        # Si existe una etiqueta en el operando se recorta
        if len([x for x in etiquetas if search(r'%s$' % x, i[3]) != None]) >= 1 \
            and 'REL' not in i:
            # Busqueda de etiqueta 
            posible = [x for x in etiquetas if search(r'%s$' % x, i[3]) != None]
            # Si exiten mas de una coincidencia se escoge la etiqueta 
            # con mas caracteres
            if len(posible) > 1:
                posible = [max(posible, key=len)]
            # Se busca la ubicacion de la etiqueta
            recorte = search(r'%s$' % posible[0], i[3])
            # Se quita la etiqueta y se anaiza el operando
            operando1 = i[3][recorte.start():]
            i[3] = i[3][:recorte.start()]
            cont += 1
        if str(i[3]) != '':
            # Si el tamaño del valor es 4 se colocan los dos valores
            if len(str(i[3])) == 4:
                operando += str(i[3]).replace(' ', '')
                cont += 2
            # Si el tamaño del valor es 1 se agrega un cero al inicio
            elif len(str(i[3])) == 1:
                operando += str(0)+str(i[3])
                cont += 1
            # Si el tamaño del valor es 3 se agrega un cero al inicio
            elif len(str(i[3])) == 3:
                operando += str(0)+str(i[3]).replace(' ', '')
                cont += 2
            # No tiene espacios entonces se puede escribir
            else:
                operando += str(i[3])
                cont += 1

    if operando1 != '':
        operando += operando1

    return instruc, operando, cont

def cuenta(start, etiq):
    cont = 0
    # Recorrido para contar los saltos
    for y in range(start ,len(info)):
        if info[y] != '':
            # Si se encuantra la etiqueta se detiene
            # y manda las unidades del salto
            if info[y][2] == 'Etiqueta':
                if etiq in info[y]:
                    return cont
            else:
                # Si la instruccion tiene una etiqueta se estima 
                # el valor de esa linea
                if type(info[y][2]) != list:
                    cont += posicionMemory(info[y].copy())[2]
                # Se contabiliza cada instruccion
                else:
                    temp1 = corresponde(info[y][1], file[y].replace(info[y][3],\
                    f'${inicio}'), info[y][2])
                    temp1[0] = to_opcode(temp1[0], temp1[1])
                    temp1.insert(0, i[0])
                    cont += posicionMemory(temp1)[2]

def saltos():
    error = False
    # Arreglo para almacenar los datos de memoria
    codigo = []
    # variable que almacena la localidad de memoria usada
    next_pose = inicio
    # Recorrido del conjunto de instrucciones
    for y, i in enumerate(info):
        if i != '':
            # Instruccion especial que no tiene opcode
            if i[2] == 'FCB':
                codigo.append([y, i[1], i[2], '', i[3]]) 
            # Etiqueta especial se cambia el inicio 
            # de localidades de memoria 
            elif i[1] == 'ORG':
                next_pose = i[2]
                inicios.append(i)
                info[y] = ''
                codigo.append(info[y])
            # Si es etiqueta se agrega con formato especial
            elif i[2] == 'Etiqueta':
                codigo.append([i[0], next_pose.upper(), i[2], i[1]])
            # Se agrega la posicion de memporia correspondiente
            elif i[2] != 'Etiqueta' and type(i[2]) != list:
                instruc, operando, cont = posicionMemory(i.copy())
                # Se almacena los datos de la linea de codigo y se actualiza
                # el estado siguiente
                codigo.append([i[0], next_pose.upper(), i[2], instruc, operando])
                next_pose = hex(int(next_pose, 16)+cont)[2:]
            # Se busca la localidad de memoria correspondiente 
            # a la etiqueta puesta
            elif type(i[2]) == list:
                # Se busca si ya aparecio esa etiqueta
                check = [x for x in codigo if i[3] in x and x[2] == 'Etiqueta']
                # Si ya aparecio esa etiqueta
                if len(check) == 1:
                    check = corresponde(i[1], file[i[0]].replace(i[3],\
                        f'${check[0][1]}'), i[2])
                    if check[1] != 'ERROR':
                        check[0] = to_opcode(check[0], check[1])
                        check.insert(0, i[0])
                        instruc, operando, cont = posicionMemory(check)
                        codigo.append([i[0], next_pose.upper(), check[2], instruc, operando])
                        next_pose = hex(int(next_pose, 16)+cont)[2:]
                    else:
                        error = True
                # Si no a aparecido esa etiqueta
                else:
                    check = corresponde(i[1], file[i[0]].replace(i[3],\
                        f'${hex(int(next_pose, 16)+cuenta(y, i[3]))[2:]}'), i[2])
                    if check[1] != 'ERROR':
                        check[0] = to_opcode(check[0], check[1])
                        check.insert(0, i[0])
                        instruc, operando, cont = posicionMemory(check)
                        codigo.append([i[0], next_pose.upper(), check[2], instruc, operando])
                        next_pose = hex(int(next_pose, 16)+cont)[2:]
                    else:
                        error = True
            # Cualquier otro caso
            else:
                codigo.append(i)
        # Cualquier otro caso
        else:
            codigo.append(i)

    # Se realiza el calculo del salto
    for y, i in enumerate(codigo):
        # Salto de directiva Relativa
        if i != '' and 'REL' in i[2]:
            for j in codigo:
                if j != '' and i[4].replace(' ', '') in j[3].replace(' ', ''):
                    desp = int(j[1], 16) - (int(i[1], 16)+int('2', 16))
                    # Si el valor del salto es mayor a 128 o menor a -127
                    # se notifica del error salto muy largo
                    if desp > 128 or desp < -127:
                        info[y][2] = 'ERROR'
                        info[y][3] = 8
                        error = True
                        return error, codigo
                    # Si no, solo se coloca el valor del salto
                    # usando una mascara de 8 bits para reducir el numero
                    # de F's
                    else:
                        desp = hex(desp & (2**8-1))[2:].upper()
                        if len(desp) < 2:
                            desp = '0'+desp
                        codigo[y][4] = desp
                        break
        # Salto de cualquier otra directiva
        elif i != '' and i[2] != 'Etiqueta' \
            and len([x for x in etiquetas if search(r'%s$' % x, i[4]) != None]) >= 1:
            # Busqueda de etiqueta 
            posible = [x for x in etiquetas if search(r'%s$' % x, i[4]) != None]
            # Si exiten mas de una coincidencia se escoge la etiqueta 
            # con mas caracteres
            if len(posible) > 1:
                posible = [max(posible, key=len)]
            # Se realiza un recorrido en el arreglo codigo para buscar 
            # la localidad de memoria 
            for j in codigo:
                if j != '' and posible[0] in j[3].replace(' ', ''):
                    # Se busca la proxima linea de codigo para 
                    # obtener la localidad de memoria 
                    for t in range(y+1, len(codigo)):
                        if codigo[t] != '':
                            desp = int(j[1], 16) - int(codigo[t][1], 16)
                            break
                    # Si el valor del salto es mayor a 128 o menor a -127
                    # se notifica del error salto muy largo
                    if desp > 128 or desp < -127:
                        info[y][2] = 'ERROR'
                        info[y][3] = 8
                        error = True
                        return error, codigo
                    # Si no, solo se coloca el valor del salto
                    # usando una mascara de 8 bits para reducir el numero
                    # de F's
                    else:
                        recor = search(r'%s$' % posible[0], codigo[y][4])
                        desp = hex(desp & (2**8-1))[2:].upper()
                        if len(desp) < 2:
                            desp = '0'+desp
                        codigo[y][4] = codigo[y][4][:recor.start()]+desp
                        break
    # Si no hay errores se regresa el arreglo
    # con los datos actualizados

    return error, codigo

# Datos mostrados al usuario
parser = arg.ArgumentParser(prog='Compilador para el micro MC68HC11',\
    description='Si el codigo esta bien, se crearan dos archivos html,'
        +' en caso de encontrar algun error se creara un txt.',
        formatter_class=arg.RawTextHelpFormatter)
# Argumentos esperados
parser.add_argument('-f', metavar='Archivo.asm',type=str,\
    help='Ej.   "-f ./archivo.asm" ', default = None)
args = parser.parse_args()
if args.f is None:
    parser.print_help()
    exit()
elif args.f:
    root, extension = path.splitext(args.f)
    if extension.lower() not in ['.asm', '.asc']:
        print('Extension de archivo incorrecta')
        exit()
    try:
        open(args.f)
    except FileNotFoundError:
        print("No se encontro el archivo")
        exit()

# Intenta abrir el archivo con codigo
with open(args.f) as file:
    # Sustituir valores de constantes y variables
    file = susValue(file)
    # Bandera para saber si existen errores
    errores = False
    # Bandera para saber si hay final
    end = False
    # Arreglo de data
    info = []
    # memoria de subrutina
    subrun = ''
    # Recorremos todas las lineas de codigo
    for cont, i in enumerate(file):
        if search(r'\*.*$', i) != None:
            i = i[:search(r'\*.*$', i).start()]
        if search(r' +$', i) != None:
            i = i[:search(r' +$', i).start()]
        # Salimos del recorrido si se encuentra el termino del codigo
        if 'end' in i and search(r'^\*.*end', i) == None:
            end = True
            info.append('')
            break
        # Salta ORG
        if 'org' in i and search(r'^\*.*org', i) == None and inicio == '':
            busq = search(r'\$[a-f0-9]{1,}', i)
            if busq == None:
                info.append([cont, 'ORG', 'ERROR', 2])
                inicio = ' '
            else:
                if formaterMemory(i[busq.start():].replace(' ', '')) == None or\
                    int(formaterMemory(i[busq.start():].replace(' ', '')), 16) > int('FFFF', 16):
                    # Error por magnitud erronea
                    info.append([cont, 'ORG', 'ERROR', 7])
                    inicio = ' '
                else:
                    inicio = i[busq.start()+1:].replace(' ', '')
                    info.append('')
        elif 'org' in i and search(r'^\*.*org', i) == None and inicio != '':
            busq = search(r'\$[a-f0-9]{1,}', i)
            if busq == None:
                info.append([cont, 'ORG', 'ERROR', 2])
            else:
                if formaterMemory(i[busq.start():].replace(' ', '')) == None or\
                    int(formaterMemory(i[busq.start():].replace(' ', '')), 16) > int('FFFF', 16):
                    # Error por magnitud erronea
                    info.append([cont, 'ORG', 'ERROR', 7])
                else:
                    subrun = i[busq.start()+1:].replace(' ', '')
                    info.append([cont, 'ORG', subrun])
        # Cadena vacia
        elif not i:
            info.append('')
        # Salta comentario de linea
        elif search(r'^[ ]*\*.', i) != None:
            info.append('')
        # Salta salto de linea
        elif search(r'^\n$', i):
            info.append('')
        # Varios espacios sin sentido
        elif search(r'^[ ]*$', i) != None:
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
        errores = True
        info.append(['ERROR', 10])
    # Realizamos el calculo de salto si existe
    # instruccion relativa, sin errores previos
    if True in [True for x in info if 'REL' in x or 'Etiqueta'] \
        and errores == False:
        errores, codigo = saltos()

# Se verifica si hay errores
if errores:
    contError = 0
    # Aviso de error
    print('ERROR')
    # Se crea un archivo especial para marcar los errores
    with open('errores.txt', 'w') as correct:
    # Se vuelve a recorrer el archivo inicial
        with open(args.f) as file:
            file = array([x[1] for x in enumerate(file)])
            for cont, i in enumerate(file):
                # Se escribe el mismo codigo
                correct.write(f'{i}')
                # Se escribe el error si existe
                if 'ERROR' in info[cont]:
                    if cont != len(file)-1:
                        correct.write(f'{error[str(info[cont][3])]}\n')
                    else:
                        correct.write(f'\n{error[str(info[cont][3])]}\n')
                    contError += 1
            # Error por falta de end
            if len(info) > len(file):
                correct.write(f'\n{error[str(info[len(info)-1][1])]}')
                contError += 1
    print(f'Se encontro {contError} error' if contError == 1 else f'Se encontro {contError} errores')
else:
    print('SUCCES')
    Lst()
    s19()