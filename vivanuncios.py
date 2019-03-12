from bs4 import BeautifulSoup
from selenium import webdriver
import requests
import pandas as pd
import time
import re
from statistics import mean
from re import sub
from decimal import Decimal

UBICACION = 'culiacan'

# Set para almacenar las diferentes fuentes de publicaciones
main_urls = set()

# Set para almacenar las diferentes pestañas de todas las fuentes
set_pestañas = set()

# Set para almacenar todos los dierentes URL de las publicaciones
set_urls = set()

# Pagina principal de vivanuncios, su treeview
page_link = []
page_link.append('https://www.vivanuncios.com.mx/sitemap_related0.xml')
page_link.append('https://www.vivanuncios.com.mx/sitemap_popular0.xml')
page_link.append('https://www.vivanuncios.com.mx/sitemap_loccat0.xml')
page_link.append('https://www.vivanuncios.com.mx/sitemap_loccatatt0.xml')
main_urls.add('https://www.vivanuncios.com.mx/s-venta-inmuebles/culiacan/v1c1097l11869p1')

driver = webdriver.PhantomJS()

# Recorrer todos las diferentes fuentes de informacion
for page in page_link:
    # Obtener el html de la pagina
    driver.get(page)
    html = driver.page_source
    page_content_main =  BeautifulSoup(html, features="html.parser")

    # Obtener todos los link de las paginas del treeview
    locations = page_content_main.find_all(lambda tag: tag.name == 'loc')
    for location in locations:
        location_url = location.text
        buscar_ubicacion = re.findall(r"\b" + UBICACION + r"\b", location_url)
        if(len(buscar_ubicacion) > 0):
            main_urls.add(location_url)

counter = 0
# Recorrer todas las paginas donde existen publicaciones
for url in main_urls:
    driver.get(url)
    html = driver.page_source
    page_content = BeautifulSoup(html, features="html.parser")

    print("Url de las principales:       " + url + '      ' + str(counter))
    set_pestañas.add(url)

    # Numero de pestañas
    try:
        pestañas = page_content.find(lambda tag: tag.name == 'div' and tag.get('class') == ['desktop-pagination'])
        pestañas = pestañas.find_all(lambda tag: tag.name == 'a')
    except:
        pestañas = 0

    numero_pestañas = 0

    # Numero de pestañas ya como numero
    try:
        for pestaña in pestañas:
            if 'pag-box-last' in pestaña.get('class', ''):
                ultima_pestaña = pestaña.get('href')
                numero_pestañas = re.search('/page-(.+?)/', ultima_pestaña).group(1)
            else:
                ultima_pestaña = pestañas[len(pestañas)-2].get("href")
                numero_pestañas = re.search('/page-(.+?)/', ultima_pestaña).group(1)
    except:
        numero_pestañas = 0

    print(numero_pestañas)
    for pestaña in range(1, int(numero_pestañas)+1):
        page_link = ultima_pestaña
        aux = re.sub(r'/page-(.+?)/', '/page-' + str(pestaña) + '/', page_link)
        #aux = "page-" + str(pestaña) + "/"
        aux = 'https://www.vivanuncios.com.mx' + aux
        aux_page  = aux.split('/')
        is_first_p = False
        aux_page_number = ''
        for char in aux_page[len(aux_page)-1][::-1]:
            if(char == 'p'):
                is_first_p = True
            if(is_first_p):
                aux_page_number += char
        aux_page_number = ''.join(reversed(aux_page_number))
        aux_page[len(aux_page)-1] = aux_page_number + str(pestaña)
        aux = '/'.join(aux_page)
        print(aux)
        # aux = aux[:-1]
        # aux = aux + str(pestaña)
        # print(aux)
        set_pestañas.add(aux)

    print("Url de las publicaciones: " + str(len(set_pestañas)))
    counter = counter + 1

counter = 0
for urls in set_pestañas:
    driver.get(urls)
    html = driver.page_source
    page_content_main =  BeautifulSoup(html)

    publicaciones = page_content_main.find_all('meta', attrs={'itemprop': 'url'})

    print("---------------------------------------------Pagina Num:" + str(counter) + "    " + str(len(publicaciones)))
    print(urls)
    print('\n')

    for i in range(0, len(publicaciones)):
        if(publicaciones[i]["content"] not in set_pestañas):
            set_urls.add(publicaciones[i]["content"])
    
    counter = counter + 1

    #with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'max_colwidth', 800):
    #    a = list(set_urls)
    #    df = pd.DataFrame(a)
    #    print(df)

    print(len(set_pestañas))

first = 0
print("INICIALIZANDO SCRAPEO")
# Iterar en las publicaciones
for i in set_urls:
    # Obtenemos el link de la pagina
    page_link = i
    print(i)
    driver.get(page_link)
    html = driver.page_source
    page_content = BeautifulSoup(html)

    # Buscamos todos los divs que tengan de clase 'category' que es donde esta la informacion de "Detalles Generales"
    try:
        category_containers = page_content.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ['category'])
    except:
        pass

    # Buscamos todos los divs que tengan de clase 'amenities-chips' que es donde esta la informacion para las amenidades
    try:
        amenidades_containers = page_content.find_all('div', attrs={"class":"amenities-chips"})
    except:
        pass

    # Extraemos el precio del anuncio
    try:
        precio_anuncio = page_content.find('div', attrs={"class":"price"})
    except:
        pass

    try:
        precio_anuncio = precio_anuncio.find('span', attrs={"class":"ad-price"}).text
    except:
        pass

    spans = {}
    amenidades = []
    precio = []

    # Recorremos todas las categorias dentro de "Detalles Generales"
    for i in category_containers:
        try:
            # La informacion esta principalmente en los spans con clase 'pri-props-name' y 'pri-props-value'
            prop = i.find(lambda tag: tag.name == 'span' and tag.get('class') == ['pri-props-name']).text
            value = i.find(lambda tag: tag.name == 'span' and tag.get('class') == ['pri-props-value']).text
            if(prop == 'Metros Cuadrados:' or prop == 'Superficie:'):
                value = re.findall(r'\d+', value)
                value.remove('2')
                value = mean(int(n) if n else 0 for n in value)
            spans[prop] = value
        # Si se encuentra un error de indice le agregamos un valor de 0
        except IndexError:
            spans[i.find('span',attrs={"class":"pri-props-name"}).text] = 0
        except: 
            pass

    # Recorremos todas las amenidades
    for i in range(0, len(amenidades_containers)):
        # La informacion de las amenidades se encuentra en 'amenities-label'
        try:
            amenidades.append(page_content.find_all(lambda tag: tag.name == 'div' and tag.get('class') == ['amenities-label'])[i].text)
        except:
            pass

    # Extraemos el precio y lo borramos los espacios vacios
    try:
        precio.append(precio_anuncio.strip())
    except:
        pass

    try:
        titulo_anuncio = page_content.find(lambda tag: tag.name == 'div' and tag.get('class') == ['revip-summary'])
        titulo_anuncio = titulo_anuncio.find(lambda tag: tag.name == 'div' and tag.get('class') == ['title']).text
    except:
        try:
            titulo_anuncio = page_content.find(lambda tag: tag.name == 'div' and tag.get('class') == ['revip-summary'])
            titulo_anuncio = titulo_anuncio.find(lambda tag: tag.name == 'div' and tag.get('class') == ['title', 'title-urgent-ad']).text
        except:
            pass

    # Obtener la ubicacion de la casa
    try:
        descripcion_anuncio = page_content.find(lambda tag: tag.name == 'div' and tag.get('class') == ['revip-description'])
        descripcion_anuncio = descripcion_anuncio.find(lambda tag: tag.name == 'div' and tag.get('class') == ['description-content']).text
        ubicacion_anuncio = page_content.find(lambda tag: tag.name == 'div' and tag.get('class') == ['revip-map'])
        ubicacion_anuncio = ubicacion_anuncio.find(lambda tag: tag.name == 'img' and tag.get('class') == ['signed-map-image']).get('src')
        ubicacion_anuncio = re.search('center=(.+?)&', ubicacion_anuncio).group(1)
    except:
        pass

    #Extraemos el precio y lo borramos los espacios vacios
    try:
        precio = precio_anuncio.strip()
    except:
        pass

    if(precio):
        precio = precio.split()

    try:
        if(precio[1] == 'USD' or precio[1] == 'usd'):
            dolar = 1
    except:
        dolar = 0

    try:
        if(precio[len(precio)-1] == 'K'):
            precio_final = Decimal(sub(r'[^\d.]', '', precio[0])) * 1000
        elif(precio[len(precio)-1] == 'M'):
            precio_final = Decimal(sub(r'[^\d.]', '', precio[0])) * 1000000
        else: 
            precio_final = Decimal(sub(r'[^\d.]', '', precio[0]))
            precio = precio_final
        precio = precio_final
    except:
        pass

    if(amenidades == []):
        amenidades = ""

    data = {'Titulo': titulo_anuncio, 'Precio': precio, 'Descripcion': descripcion_anuncio,'Ubicacion': ubicacion_anuncio, 'Amenidades': [amenidades]}
    data_url = {'Url': page_link}
    data_dolar = {'Dolar': dolar}
    if (first == 0):
        df_1 = pd.DataFrame(data=data, index=[0])
        df_2 = pd.DataFrame(data=spans, index=[0])
        df_url = pd.DataFrame(data=data_url, index=[0])
        df_dolar = pd.DataFrame(data = data_dolar, index=[0])
        df3 = pd.concat([df_1, df_2], axis=1, join='inner')
        df3 = pd.concat([df3, df_url],axis=1, join='inner')
        df3 = pd.concat([df3, df_dolar],axis=1, join='inner')
        first = 1
    else:
        df_1 = df_1.append(data, ignore_index=[True])
        df_2 = df_2.append(spans, ignore_index=[True])
        df_url = df_url.append(data_url, ignore_index=[True])
        df_dolar = df_dolar.append(data_dolar, ignore_index=[True])
        df3 = pd.concat([df_1, df_2], axis=1, join='inner')
        df3 = pd.concat([df3, df_url],axis=1, join='inner')
        df3 = pd.concat([df3, df_dolar],axis=1, join='inner')

    print(df3)
    print(len(df3))

    if(len(df3) >= 1):
        df3.to_csv('pruebas.csv')