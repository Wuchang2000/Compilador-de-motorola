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
            # if loc in etiquetas and 'REL' not in clase:
            #     return [instruccion, clase, loc]
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
            # if loc in etiquetas and 'REL' not in clase:
            #     return [instruccion, clase, loc]
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
            # if loc in etiquetas and 'REL' not in clase:
            #     return [instruccion, clase, loc]
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


# def divisionHexa(i, nex_pos, idx):
#     num = []
#     if cont+2 > 16:
#         # Escritura de parte alta del hexa
#         high = i[idx].split(' ')[0]
#         # print(f'{high} ')
#         # nex_pos = hex(int(nex_pos, 16)+16)
#         # # Escritura de nueva posicion del hexa
#         # # print(f'\n<{nex_pos[2:]}> ')
#         # cont = 0
#         low = i[idx].split(' ')[1]
#         # Escritura de parte baja del hexa
#         # print(f'{low} ')
#         # cont += 1
#         num.append(high)
#         num.append(low)
#     # Se colocan los dos hexa
#     else:
#         # print(f'{i[idx]} ')
#         num.append(i[idx])
#         cont += 2

#     return cont, nex_pos, num

def s19():
    # genera el arhivo s19
    with open('./code.s19', 'w') as file:
        # Escribimos el lugar en memoria donde inicia el programa
        file.write(f'<{inicio}> ')
        # cont = 0
        # nex_pos = inicio
        # info2 = [x for x in info if x != '']
        # cont2 = len(info2)
        # # Recorremos el arreglo de operaciones
        # for i in info:
        #     try:
        #     # Si es una etiqueta la saltamos
        #         if len(i) > 1 and i[2] != 'Etiqueta':
        #             # Si tiene tamaño 3 significa que tiene un espacio
        #             # y es un numero hexa de dos caracteres
        #             if type(i[1]) == str and len(i[1]) == 3:
        #                 l = i[1].replace(' ', '')
        #                 file.write(f'{l} ')
        #                 cont += 1
        #             # Si tiene tamaño 5 significa que tiene un espacio
        #             # y es dos numeros hexa de dos caracteres
        #             elif type(i[1]) == str and len(i[1]) == 5:
        #                 # Si se pasa de los 16 bits al colocar dos hexa
        #                 # se hace un salto de linea (uno y uno)
        #                 cont, nex_pos = divisionHexa(file, cont, i, nex_pos, 1)
        #             # No tiene espacios entonces se puede escribir
        #             else:
        #                 file.write(f'{i[1]} ')
        #                 cont += 1
        #             # Seccion que coloca los valores hexadecimales
        #             # de las instrucciones
        #             if len(i) > 3:
        #                 # Si el tamaño del valor es 4 se colocan los dos valores
        #                 if len(i[3]) == 4:
        #                     i[3] = f'{i[3][0:2]} {i[3][2:]}'
        #                     cont, nex_pos = divisionHexa(file, cont, i, nex_pos, 3)
        #                 # Si el tamaño del valor es 1 se agrega un cero al inicio
        #                 elif len(i[3]) == 1:
        #                     file.write(f'0{i[3]} ')
        #                     cont += 1
        #                 # Si el tamaño del valor es 3 se agrega un cero al inicio
        #                 elif len(i[3]) == 3:
        #                     i[3] = f'0{i[3][1]} {i[3][2:]}'
        #                     cont, nex_pos = divisionHexa(file, cont, i, nex_pos, 3)
        #                 # No tiene espacios entonces se puede escribir
        #                 else:
        #                     file.write(f'{i[3]} ')
        #                     cont += 1
        #             # Si ya se escribieron 16 caracteres se
        #             # hace un salto de linea con la nueva posicion en memoria
        #             # pero solo si todavia existen lineas analizables
        #             if cont == 16 and cont2-1 > 0:
        #                 nex_pos = hex(int(nex_pos, 16)+16)
        #                 file.write(f'\n<{nex_pos[2:]}> ')
        #                 cont = 0
        #         cont2 -= 1
        #     except:
        #         pass

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
        # Si el tamaño del valor es 4 se colocan los dos valores
        if len([x for x in etiquetas if search(r'%s$' % x, i[3]) != None]) >= 1 \
            and 'REL' not in i:
            for j in etiquetas:
                recorte = search(r'%s$' % j, i[3])
                if recorte != None:
                    operando1 = i[3][recorte.start():]
                    i[3] = i[3][:recorte.start()]
                    cont += 1
                    break
        if str(i[3]) != '':
            if len(str(i[3])) == 4:
                operando += str(i[3]).replace(' ', '')
                # if search(r'^[0]{2,4}.{0,2}$', operando) != None:
                #     operando = operando[2:]
                #     cont +=1
                # else:
                #     cont += 2
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

# jump = []

# def recuCuenta(start, etiq):
#     return cuenta(start, etiq)

def cuenta(start, etiq):
    # control = False
    cont = 0
    # temp1 = 0
    for y in range(start ,len(info)):
        if info[y] != '':
            # print(f'{y}:{i}')
            if info[y][2] == 'Etiqueta':
                if etiq in info[y]:
                    # print(f'Salgo {info[y][1]} con {cont}')
                    # jump.append([etiq, cont])
                    # return cont, True
                    return cont
            else:
                if type(info[y][2]) != list:
                    # if info[y][2] == 'REL':
                    #     cont += posicionMemory(info[y].copy())[2]
                    # else:
                    #     cont += posicionMemory(info[y])[2]
                    cont += posicionMemory(info[y])[2]
                else:
                    temp1 = corresponde(info[y][1], file[y].replace(info[y][3],\
                    f'${inicio}'), info[y][2])
                    temp1[0] = to_opcode(temp1[0], temp1[1])
                    temp1.insert(0, i[0])
                    cont += posicionMemory(temp1)[2]
                    # if control == False:
                    #     # print(f'Encontre {info[y][3]} con {cont}')
                    #     temp1, control = recuCuenta(y+1, info[y][3])
    # cont = 0
    # for y in range(start , 0, -1):
    #     if info[y] != '':
    #         # print(f'{y}:{i}')
    #         if info[y][2] == 'Etiqueta':
    #             if etiq in info[y]:
    #                 # print(f'Salgo {info[y][1]} con {cont}')
    #                 jump.append([etiq, cont])
    #                 return cont, True
    #         else:
    #             if type(info[y][2]) != list:
    #                 temp1 += posicionMemory(info[y])[2]
    #             else:
    #                 if control == False:
    #                     # print(f'Encontre {info[y][3]} con {cont}')
    #                     temp1, control = recuCuenta(y+1, info[y][3])

def saltos():
    error = False
    # Arreglo para almacenar los datos de memoria
    codigo = []
    # variable que almacena la localidad de memoria usada
    next_pose = inicio
    # Recorrido del conjunto de instrucciones
    for y, i in enumerate(info):
        if i != '' and i[2] == 'FCB':
            codigo.append([y, i[1], i[2], '', i[3]])
        elif i != '' and i[1] == 'ORG':
            next_pose = i[2]
            info[y] = ''
            codigo.append(info[y])
        # Se analizan los datos que son instrucciones y no las etiquetas
        elif i != '' and i[2] != 'Etiqueta' and type(i[2]) != list:
            instruc, operando, cont = posicionMemory(i)
            # Se almacena los datos de la linea de codigo y se actualiza
            # el estado siguiente
            codigo.append([i[0], next_pose.upper(), i[2], instruc, operando])
            next_pose = hex(int(next_pose, 16)+cont)[2:]
        # Si es etiqueta se almacena con formato especial
        elif i != '' and i[2] == 'Etiqueta':
            codigo.append([i[0], next_pose.upper(), i[2], i[1]])
        # Si falta saber la posicion de la etiqueta
        elif i != '' and type(i[2]) == list:
            check = [x for x in codigo if i[3] in x and x[2] == 'Etiqueta']
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
            else:
                check = corresponde(i[1], file[i[0]].replace(i[3],\
                    f'${hex(int(next_pose, 16)+cuenta(y+1, i[3]))[2:]}'), i[2])
                if check[1] != 'ERROR':
                    check[0] = to_opcode(check[0], check[1])
                    check.insert(0, i[0])
                    instruc, operando, cont = posicionMemory(check)
                    codigo.append([i[0], next_pose.upper(), check[2], instruc, operando])
                    next_pose = hex(int(next_pose, 16)+cont)[2:]
                else:
                    error = True
        # Si es cualquier otra cosa se copia igual
        else:
            codigo.append(i)
    
    # Se realiza el calculo del salto
    for y, i in enumerate(codigo):
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
        elif i != '' and i[2] != 'Etiqueta' \
            and len([x for x in etiquetas if search(r'%s$' % x, i[4]) != None]) >= 1:
            posible = [x for x in etiquetas if search(r'%s$' % x, i[4]) != None]
            for j in codigo:
                if j != '' and posible[0] in j[3].replace(' ', ''):
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
                        # print(codigo[y][4][:recor.start()]+hex(desp & (2**8-1))[2:].upper())
                        codigo[y][4] = codigo[y][4][:recor.start()]+desp
    # Si no hay errores se regresa el arreglo
    # con los datos actualizados
    return error, codigo

parser = arg.ArgumentParser(prog='Compilador para el micro MC68HC11',\
    description='Si el codigo esta bien, se crearan dos archivos html,'
        +' en caso de encontrar algun error se creara un txt.',
        formatter_class=arg.RawTextHelpFormatter)
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
    # s19()
    Lst()