from format_song_files.utils import *
import json
import os
import shutil
from insert_informations import deleteTags, setTags
from concurrent.futures import ProcessPoolExecutor, as_completed

from format_song_files.visualize import barChart
import mutagen

"""
{
    "SourceFile": "E:\\music\\1994 (Nightcore) - Alec Benjamin (2018).opus",
    "ExifTool:ExifTool Version Number": "13.59",
    "File:File Name": "1994 (Nightcore) - Alec Benjamin (2018).opus",
    "File:Directory": "E:/music",
    "File:File Size": 3278356,
    "File:File Modification Date/Time": "2026:08:16 21:44:27+02:00",
    "File:File Access Date/Time": "2026:08:20 09:37:52+02:00",
    "File:File Creation Date/Time": "2026:08:16 21:23:31+02:00",
    "File:File Permissions": 100666,
    "File:File Type": "OPUS",
    "File:File Type Extension": "OPUS",
    "File:MIME Type": "audio/ogg",
    "Opus:Opus Version": 1,
    "Opus:Audio Channels": 2,
    "Opus:Sample Rate": 48000,
    "Opus:Output Gain": 1,
    "Vorbis:Vendor": "Lavf63.5.101",
    "Vorbis:Encoder": "Lavf63.5.101",
    "Vorbis:Title": "1994 (Nightcore)",
    "Vorbis:Artist": "Alec Benjamin",
    "Vorbis:Year": 2018,
    "Vorbis:Genre": [
        "1994 (Nightcore)",
        "Alec Benjamin",
        2018,
        "Pop",
        "Singer-Songwriter",
        "Nightcore",
        "Nightcore",
        "Remix",
        "Sped Up",
        "Nostalgic",
        "Reflective",
        "Bittersweet",
        "Coming-of-age",
        "English",
        "USA",
        "2010s",
        "Fan art featuring My Hero Academia's Izuku Midoriya",
        "Original by Alec Benjamin"
    ],
    "Vorbis:Style": [
        "Nightcore",
        "Remix",
        "Sped Up"
    ],
    "Vorbis:Mood": [
        "Nostalgic",
        "Reflective",
        "Bittersweet",
        "Coming-of-age"
    ],
    "Vorbis:Language": "English",
    "Vorbis:Country": "USA",
    "Vorbis:Decade": "2010s",
    "Vorbis:Comment": [
        "Fan art featuring My Hero Academia's Izuku Midoriya",
        "Original by Alec Benjamin"
    ],
    "Vorbis:Real Genre": [
        "Pop",
        "Singer-Songwriter",
        "Nightcore"
    ],
    "FLAC:Picture Type": 3,
    "FLAC:Picture MIME Type": "image/png",
    "FLAC:Picture Description": "",
    "FLAC:Picture Width": 1280,
    "FLAC:Picture Height": 720,
    "FLAC:Picture Bits Per Pixel": 0,
    "FLAC:Picture Indexed Colors": 0,
    "FLAC:Picture Length": 422669,
    "FLAC:Picture": "(Binary data 422669 bytes, use -b option to extract)"
}
"""


def getAllNightCoreTitles():
    # wait to have handle all nightcore before so they have the tags
    config = readConfig()
    infos = extractInfosWithTags(r'E:\music', {'Vorbis:Genre':'NightCore'}, key_operator='or', exiftool_exe_path=config['global']['exiftool_exe_path'])
    source_files = infosSingleFilter(infos, key='SourceFile')
    print(source_files)
    
def getAllGenres():
    config = readConfig()
    tags = getAllTags(r'E:\music', keys='Vorbis:Genre', exiftool_exe_path=config['global']['exiftool_exe_path'])
    print(tags)
    
def updateAllTags():
    config = readConfig()
    styles = getAllTags(r'E:\music', keys='Vorbis:Style', exiftool_exe_path=config['global']['exiftool_exe_path'])
    moods = getAllTags(r'E:\music', keys='Vorbis:Mood', exiftool_exe_path=config['global']['exiftool_exe_path'])
    genres = getAllTags(r'E:\music', keys='Vorbis:Real Genre', exiftool_exe_path=config['global']['exiftool_exe_path'])
    
    obj = {
        "style"    : list(styles   ),
        "mood"     : list(moods    ),
        "genre"    : list(genres   )
    }
    
    with open("all_tags.json", "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4)
        
def correctSemicolonTags():
    
    config = readConfig()
    exiftool_exe_path = config['global']['exiftool_exe_path']
    dir_path = r'E:\music'
    keys = ["Vorbis:Genre", "Vorbis:Style", "Vorbis:Mood", "Vorbis:Comment", "Vorbis:Real Genre"]
    
    with exiftool.ExifToolHelper(executable=exiftool_exe_path, encoding="utf-8") as et:
        for entry in os.scandir(dir_path):
            if not entry.is_file():
                continue
            
            infos = extractInformation(entry.path, et)

            for key in keys:
                if key not in infos:
                    logger.warning(
                        "Key %s is not present in %s",
                        key,
                        os.path.basename(entry.path)
                    )
                    continue
                
                raw_values = infos[key] if isinstance(infos[key], list) else [infos[key]]
                
                # verify if an element have a semicolon
                has_semicolon = any(isinstance(v, str) and ';' in v for v in raw_values)
                if not has_semicolon:
                    continue

                # reconstruct the list, split ; and convert all to str
                clean_values = []
                for v in raw_values:
                    v_str = str(v)
                    if ';' in v_str:
                        clean_values.extend([part.strip() for part in v_str.split(';') if part.strip()])
                    else:
                        clean_values.append(v_str.strip())

                # Use SourceFile or current path
                target_path = infos.get('SourceFile', entry.path)
                audio = mutagen.File(target_path, easy=True)
                
                simple_key = key.split(':')[1].lower().strip().replace(' ','_')
                deleteTags(audio, simple_key)
                setTags(audio, {simple_key: list(set(clean_values))})
                
                audio.save()
                
def restartDeleteAllTags():
    config = readConfig()
    exiftool_exe_path = config['global']['exiftool_exe_path']
    dir_path = r'E:\music'
    keys = ["Vorbis:Genre", "Vorbis:Style", "Vorbis:Mood", "Vorbis:Comment", "Vorbis:Real Genre"]
    with exiftool.ExifToolHelper(executable=exiftool_exe_path, encoding="utf-8") as et:
        for entry in os.scandir(dir_path):
            if not entry.is_file():
                continue
                
            audio = mutagen.File(entry.path, easy=True)
            deleteTags(audio, [key.split(':')[1].lower().strip().replace(' ','_') for key in keys])
            
            audio.save()
            
def sortAllPossibleTags():
    path = 'all_possible_tags.json'
    with open(path, 'r', encoding='utf-8') as f:
        apt = json.load(f)
        
    for k, v in apt.items():
        apt[k] = sorted(apt[k])
        
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(apt, f, indent=4)
        
def restructureTheServer():
    config = readConfig()
    exiftool_exe_path = config['global']['exiftool_exe_path']
    dir_path = r'E:\music'
    
    plexStructure(
        path=dir_path,
        exiftool_exe_path=exiftool_exe_path,
        recursive=True
    )

# replaceTagByAnotherOne(path=dir_path, 
#                            tag_reorganisation='plex',
#                            tags={
#                                 "Style":{
#                                     "Broadside Ballad"		: [("Style", "Ballad")],			
#                                     "Character Ballad"		: [("Style", "Ballad")],			
#                                     "Child Ballad"			: [("Style", "Ballad")],		
#                                     "Cinematic Ballad"		: [("Style", "Ballad")],			
#                                     "Cross-Dressing Ballad"	: [("Style", "Ballad")],				
#                                     "Irish Ballad"			: [("Style", "Ballad")],		
#                                     "Mourning Ballad"		: [("Style", "Ballad")],			
#                                     "Pirate Ballad"			: [("Style", "Ballad")],		
#                                     "Scottish Ballad"		: [("Style", "Ballad")],			
#                                     "Solo Ballad"			: [("Style", "Ballad")],
#                                     "Piano Arrangement"		: [("Genre", "Piano"), ("Style", "Instrumental")],									
#                                     "Solo Piano"			: [("Genre", "Piano"), ("Style", "Instrumental")],								
#                                     "Fingerstyle Guitar"	: [("Genre", "Guitar"), ("Style", "Instrumental")],										
#                                     "Fan Compilation"		: [("Style", "Fan-Made"), ("Style", "Compilation")],											
#                                     "Launch Cinematic"		: [("Style", "Cinematic"), ("Style", "Trailer")],									
#                                     "Background Score"		: [("Style", "BGM")],									
#                                     "Live Recording"		: [("Style", "Live Performance")],									
#                                     "Street Performance"	: [("Style", "Live Performance")],										
#                                     "Boogie Woogie"			: [("Genre", "Blues"), ("Genre", "Jazz")],								
#                                     "Western Swing"			: [("Genre", "Swing"), ("Genre", "Country")],								
#                                     "Swing Dance"			: [("Genre", "Swing"), ("Genre", "Country")],								
#                                     "Fantasy Folk"			: [("Genre", "Folk"), ("Mood", "Fantasy")],								
#                                     "Flamenco Palo"			: [("Genre", "Flamenco")],								
#                                     "Nautical"				: [("Genre", "Sea Shanty")],							
#                                     "Scat Singing"			: [],								
#                                     "Ceremonial Song"		: [],									
#                                     "Farewell Song"			: [],								
#                                     "NCS Release"			: [],	
#                                     "Military March"		: [("Mood", "Militaristic")],
#                                     "AMV"					: [],					
#                                     "Gun Sync"				: [],							
#                                     "English Dub"			: [],							
#                                     "Pitch-Shifted"			: [],								
#                                     "Short Film"			: [],	
#                                     "Celtic"				: [("Genre", "Celtic")],
#                                     "Waltz"					: [("Genre", "Waltz")],
#                                     "Polka"					: [("Genre", "Polka")],	
#                                     "Female voice"					: [("Genre", "Female Voice")],	
#                                     "Male voice"					: [("Genre", "Male Voice")],												
#                                 },
#                                 "Genre":{
#                                     "Shanty"				: [("Genre", "Sea Shanty")],		
#                                     "Mashup"				: [],		
#                                     "Acoustic Pop"			: [("Genre", "Acoustic"), ("Genre", "Pop")],			
#                                     "Symphonic Pop"			: [("Genre", "Orchestral"), ("Genre", "Pop")],			
#                                     "Symphonic Rock"		: [("Genre", "Orchestral"), ("Genre", "Rock")],				
#                                     "Classical Crossover"	: [("Genre", "Classical"), ("Genre", "Pop")],	
#                                     "Dark Pop"				: [("Genre", "Pop"), ("Mood", "Dark")],		
#                                     "Andalusian Folk"		: [("Genre", "Flamenco")],				
#                                     "Anglo-American Folk"	: [("Genre", "Folk")],					
#                                     "British Isles Folk"	: [("Genre", "Folk")],					
#                                     "British Naval Folk"	: [("Genre", "Folk")],					
#                                     "Cornish Folk"			: [("Genre", "Folk")],			
#                                     "Maritime Folk"			: [("Genre", "Folk")],			
#                                     "Medieval Folk"			: [("Genre", "Folk"), ("Mood", "Medieval")],			
#                                     "New Zealand Folk"		: [("Genre", "Folk")],				
#                                     "Scots-Irish Folk"		: [("Genre", "Folk")],	
#                                     "Russian Folk"			: [("Genre", "Folk")],
#                                     "Scottish Folk"			: [("Genre", "Folk")],
#                                     "Irish Folk"			: [("Genre", "Folk")],			
#                                     "Brega"					: [("Genre", "Latin"), ("Genre", "Pop")],	
#                                     "Balearic"				: [("Genre", "Electronic")],		
#                                     "Jumpstyle"				: [("Genre", "Electronic")],		
#                                     "Glitch Hop"			: [("Genre", "Electronic")],			
#                                     "Jump Blues"			: [("Genre", "Blues"), ("Genre", "Swing")],			
#                                     "Outlaw Country"		: [("Genre", "Country")],				
#                                     "Filk"					: [("Genre", "Folk")],	
#                                     "Post-Grunge"			: [("Genre", "Alternative Rock")],			
#                                     "Romantic Era"			: [("Genre", "Classical")],		
#                                     "Denpa"					: [],	
#                                     "J-Core"				: [],		
#                                     "Lambada"				: [("Genre", "Latin")],	
#                                     "English Folk"			: [("Genre", "Folk")],
#                                     "French House"			: [("Genre", "House")],
#                                     "French Pop"			: [("Genre", "Pop")],
#                                     "French Rap"			: [("Genre", "Rap")],
#                                     "Folk Metal"			: [("Genre", "Folk"), ("Genre", "Metal")],	
#                                     "Folk Pop"				: [("Genre", "Folk"), ("Genre", "Pop")],
#                                     "Meme"					: [("Style", "Meme")],
#                                 },
#                                 "Mood":{
#                                     "Fantastical"			: [("Mood", "Fantasy")],			
#                                     "Jovial"				: [("Mood", "Cheerful")],		
#                                     "Rollicking"			: [("Mood", "Rowdy")],			
#                                     "Boisterous"			: [("Mood", "Rowdy")],			
#                                     "Hearty"				: [("Mood", "Festive"), ("Mood", "Warm")],		
#                                     "Convivial"				: [("Mood", "Festive"), ("Mood", "Warm")],		
#                                     "Nonsensical"			: [("Mood", "Silly")],			
#                                     "Wry"					: [("Mood", "Witty"), ("Mood", "Ironic")],	
#                                     "Confrontational"		: [("Mood", "Provocative")],			
#                                     "Punchy"				: [("Mood", "Energetic")],		
#                                     "Stately"				: [("Mood", "Majestic"), ("Mood", "Regal")],		
#                                     "Touching"				: [("Mood", "Heartfelt")],		
#                                     "Cautionary"			: [],			
#                                     "Communal"				: [],		
#                                     "Loyal"					: [],	
#                                     "Devoted"				: [],		
#                                 }
#                             }, exiftool_exe_path=exiftool_exe_path)

def getGraphs(root:str, exiftool_exe_path:str, max_workers:int|None=0):
    from tqdm import tqdm
    if max_workers <= 0:
        for tag in tqdm(['Year', 'RealGenre', 'Style', 'Mood', 'Language', 'Country', 'Decade']):
            barChart( root, tag, exiftool_exe_path=exiftool_exe_path, save=f'./img/{tag.lower()}.jpg',verbose=1)
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            jobs = [
                executor.submit(barChart, root, tag, exiftool_exe_path=exiftool_exe_path, save=f'./img/{tag.lower()}.jpg', verbose=0) 
                for tag in ['Year', 'RealGenre', 'Style', 'Mood', 'Language', 'Country', 'Decade']
            ]
            
            for job in tqdm(as_completed(jobs), total=len(jobs)):
                job.result()
            


def splitAgregateTags(path:str, exiftool_exe_path:str, separator:str=';', keys:list[str]=['Year', 'RealGenre', 'Genre', 'Style', 'Mood', 'Language', 'Country', 'Decade']):
    total = 0
    with exiftool.ExifToolHelper(
                executable=exiftool_exe_path,
                encoding="utf-8",
            ) as et:
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                infos = extractInformation(file_path, exiftool_helper=et)
                for key in keys:
                    if not key in infos:
                        continue
                    tags_to_set = {}
                    if not isinstance(infos[key], list):
                        infos[key] = [infos[key]]
                    for tag in infos[key]:
                        
                        if separator in str(tag) and str(tag) not in ('Steins;Gate', 'Steins;Gate (2011 anime)'):
                            if key not in tags_to_set:
                                tags_to_set[key] = infos[key][:]
        
                            tags_to_set[key].remove(tag)
                            tags_to_set[key].extend([sub_tag.strip() for sub_tag in str(tag).split(separator) if sub_tag.strip() not in tags_to_set[key]])
                            
                            
                    
                    if tags_to_set: 
                        print(infos.keys())
                        
                        print(f'{key!r} - {file}')
                        print(f'From: {infos[key]}')
                        print(f'To: {tags_to_set[key]}')
                        print()
                        total +=1
                        # audio = mutagen.File(file_path, easy=True)
                        # setTags(audio, tags_to_set)
                        # audio.save()
                    
        print(total)

# utils.py

def _normalizeTagKey(key: str) -> str:
    return str(key).lower().replace('_', '').replace(' ', '').replace('-', '')

def deleteTags2(audio: mutagen.File, tags_to_delete: list[str]):
    if not tags_to_delete:
        return
    targets = {_normalizeTagKey(t) for t in tags_to_delete}
    # compare la forme normalisée de CHAQUE clé réellement présente dans le fichier,
    # plutôt qu'un match exact — attrape toutes les variantes historiques
    for existing_key in list(audio.keys()):
        if _normalizeTagKey(existing_key) in targets:
            audio.pop(existing_key, None)
            
def fixGenreStyleMoodTags(
    path: str,
    exiftool_exe_path: str,
    all_possible_tags_path: str = './all_possible_tags.json',
    separator: str = ';',
    exceptions: tuple[str, ...] = ('Steins;Gate', 'Steins;Gate (2011 anime)'),
    dry_run: bool = True,
):
    """
    Pour chaque fichier de `path` :
      1. Regroupe toutes les variantes de clé (RealGenre / Realgenre / real_genre / "REAL GENRE"...)
         sous leur vraie clé canonique : real_genre, style, mood, language, country, decade.
      2. Split toute valeur encore agrégée avec ';' en plusieurs valeurs distinctes.
      3. Filtre real_genre / style / mood pour ne garder que ce qui existe dans all_possible_tags.json.
      4. Reconstruit 'genre' (compat Plex) = concat dédupliquée de :
         real_genre + style + mood + language + country + decade.
      5. Supprime toutes les anciennes variantes de clés (y compris 'genre' pollué, quelle que
         soit sa variante) et réécrit proprement real_genre / style / mood / language / country /
         decade / genre.

    dry_run=True (défaut) : ne modifie rien, retourne juste un rapport des changements prévus.
    """
    with open(all_possible_tags_path, 'r', encoding='utf-8') as f:
        all_possible_tags = json.load(f)

    valid_genre = set(all_possible_tags.get('genre', []))
    valid_style = set(all_possible_tags.get('style', []))
    valid_mood  = set(all_possible_tags.get('mood', []))

    # clés "ingrédients" qu'on regroupe/nettoie ; 'genre' n'en fait PAS partie :
    # on le reconstruit entièrement, peu importe ce qu'il contenait avant.
    source_keys = ['real_genre', 'style', 'mood', 'language', 'country', 'decade']
    keys_to_wipe = source_keys + ['genre']  # tout ce qu'on supprime avant réécriture

    def normalize(key: str) -> str:
        return str(key).lower().replace('_', '').replace(' ', '').replace('-', '')

    canonical_by_norm = {normalize(k): k for k in source_keys}

    def splitValues(values: list) -> list:
        result = []
        for v in values:
            v_str = str(v)
            if separator in v_str and v_str not in exceptions:
                result.extend(p.strip() for p in v_str.split(separator) if p.strip())
            else:
                result.append(v_str)
        return list(set(result))

    report = {}

    with exiftool.ExifToolHelper(executable=exiftool_exe_path, encoding="utf-8") as et:
        for root, _, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    infos = extractInformation(file_path, exiftool_helper=et)

                    grouped = {k: [] for k in source_keys}
                    variant_keys_seen = {k: [] for k in source_keys}

                    for info_key, info_value in infos.items():
                        norm = normalize(info_key)
                        if norm not in canonical_by_norm:
                            continue
                        canon = canonical_by_norm[norm]
                        values = info_value if isinstance(info_value, list) else [info_value]
                        grouped[canon].extend(values)
                        variant_keys_seen[canon].append(info_key)

                    if not any(variant_keys_seen.values()):
                        continue  # rien de pertinent sur ce fichier

                    for canon in source_keys:
                        grouped[canon] = list(dict.fromkeys(splitValues(grouped[canon])))

                    before_genre = set(grouped['real_genre'])
                    before_style = set(grouped['style'])
                    before_mood  = set(grouped['mood'])

                    grouped['real_genre'] = [v for v in grouped['real_genre'] if v in valid_genre]
                    grouped['style']      = [v for v in grouped['style'] if v in valid_style]
                    grouped['mood']       = [v for v in grouped['mood'] if v in valid_mood]

                    dropped = {
                        'real_genre': sorted(before_genre - set(grouped['real_genre'])),
                        'style':      sorted(before_style - set(grouped['style'])),
                        'mood':       sorted(before_mood - set(grouped['mood'])),
                    }

                    grouped['genre'] = list(dict.fromkeys(
                        grouped['real_genre'] + grouped['style'] + grouped['mood'] +
                        grouped['language'] + grouped['country'] + grouped['decade']
                    ))

                    tags_to_set = {k: v for k, v in grouped.items() if v}
                    merged_keys = {k: v for k, v in variant_keys_seen.items() if len(v) > 1}

                    had_changes = bool(
                        any(dropped.values())
                        or merged_keys
                    )

                    if had_changes:
                        report[file_path] = {
                            'dropped': {k: v for k, v in dropped.items() if v},
                            'merged_keys': merged_keys,
                            'result': tags_to_set,
                        }

                    if dry_run:
                        continue

                    audio = mutagen.File(file_path, easy=True)
                    if audio is None:
                        logger.warning("Impossible d'ouvrir %s", file_path)
                        continue

                    deleteTags2(audio, keys_to_wipe)
                    setTags(audio, tags_to_set)
                    audio.save()

                except Exception:
                    logger.exception("Erreur sur %s", file_path)

    return report
            
if __name__ == '__main__':
    config = readConfig()
    exiftool_exe_path = config['global']['exiftool_exe_path']
    dir_path = r'E:\music'
    
    getGraphs(root=dir_path, exiftool_exe_path=exiftool_exe_path, max_workers=0)
    #splitAgregateTags(dir_path, exiftool_exe_path)
    #report = fixGenreStyleMoodTags(r'E:\music', exiftool_exe_path, dry_run=True)
    #print(json.dumps(report, indent=2, ensure_ascii=False))

    
    # with exiftool.ExifToolHelper(
    #                     executable=exiftool_exe_path,
    #                     encoding="utf-8",
    #                 ) as et:
    #         total = 0
    #         tt_RealGenre = 0
    #         tt_Realgenre = 0
    #         for root, _, files in os.walk(dir_path):
    #             for file in files:
    #                 file_path = os.path.join(root, file)
    #                 infos = extractInformation(file_path, exiftool_helper=et)
                    
    #                 real_genre = infos.get('RealGenre', [])
    #                 if not isinstance(real_genre, list):
    #                     real_genre = [real_genre]
    #                 if 'Realgenre' in infos:
    #                     print(file)
    #                     audio = mutagen.File(file_path, easy=True)
    #                     real_genre.extend(infos['Realgenre'] if isinstance(infos['Realgenre'], list) else [infos['Realgenre']])
    #                     real_genre = list(set(real_genre))
    #                     audio.pop('realgenre', None)
    #                     audio['real_genre'] = real_genre
    #                     audio.save()
                    
    
    #getGraphs(dir_path, exiftool_exe_path)
    # replaceTagByAnotherOne(path=dir_path, 
    #                        tag_reorganisation='plex',
    #                        tags={
    #                                 "RealGenre":{
    #                                 "Shanty"				: [("RealGenre", "Sea Shanty")],		
    #                                 "Mashup"				: [],		
    #                                 "Acoustic Pop"			: [("RealGenre", "Acoustic"), ("RealGenre", "Pop")],			
    #                                 "Symphonic Pop"			: [("RealGenre", "Orchestral"), ("RealGenre", "Pop")],			
    #                                 "Symphonic Rock"		: [("RealGenre", "Orchestral"), ("RealGenre", "Rock")],				
    #                                 "Classical Crossover"	: [("RealGenre", "Classical"), ("RealGenre", "Pop")],	
    #                                 "Dark Pop"				: [("RealGenre", "Pop"), ("Mood", "Dark")],		
    #                                 "Andalusian Folk"		: [("RealGenre", "Flamenco")],				
    #                                 "Anglo-American Folk"	: [("RealGenre", "Folk")],					
    #                                 "British Isles Folk"	: [("RealGenre", "Folk")],					
    #                                 "British Naval Folk"	: [("RealGenre", "Folk")],					
    #                                 "Cornish Folk"			: [("RealGenre", "Folk")],			
    #                                 "Maritime Folk"			: [("RealGenre", "Folk")],			
    #                                 "Medieval Folk"			: [("RealGenre", "Folk"), ("Mood", "Medieval")],			
    #                                 "New Zealand Folk"		: [("RealGenre", "Folk")],				
    #                                 "Scots-Irish Folk"		: [("RealGenre", "Folk")],	
    #                                 "Russian Folk"			: [("RealGenre", "Folk")],
    #                                 "Scottish Folk"			: [("RealGenre", "Folk")],
    #                                 "Irish Folk"			: [("RealGenre", "Folk")],			
    #                                 "Brega"					: [("RealGenre", "Latin"), ("RealGenre", "Pop")],	
    #                                 "Balearic"				: [("RealGenre", "Electronic")],		
    #                                 "Jumpstyle"				: [("RealGenre", "Electronic")],		
    #                                 "Glitch Hop"			: [("RealGenre", "Electronic")],			
    #                                 "Jump Blues"			: [("RealGenre", "Blues"), ("RealGenre", "Swing")],			
    #                                 "Outlaw Country"		: [("RealGenre", "Country")],				
    #                                 "Filk"					: [("RealGenre", "Folk")],	
    #                                 "Post-Grunge"			: [("RealGenre", "Alternative Rock")],			
    #                                 "Romantic Era"			: [("RealGenre", "Classical")],		
    #                                 "Denpa"					: [],	
    #                                 "J-Core"				: [],		
    #                                 "Lambada"				: [("RealGenre", "Latin")],	
    #                                 "English Folk"			: [("RealGenre", "Folk")],
    #                                 "French House"			: [("RealGenre", "House")],
    #                                 "French Pop"			: [("RealGenre", "Pop")],
    #                                 "French Rap"			: [("RealGenre", "Rap")],
    #                                 "Folk Metal"			: [("RealGenre", "Folk"), ("RealGenre", "Metal")],	
    #                                 "Folk Pop"				: [("RealGenre", "Folk"), ("RealGenre", "Pop")],
    #                                 "Meme"					: [("Style", "Meme")],
    #                             },
    #                             "Genre":{
    #                                 "Shanty"                : [("Genre", "Sea Shanty")],        
    #                                 "Mashup"                : [],       
    #                                 "Acoustic Pop"          : [("Genre", "Acoustic"), ("Genre", "Pop")],            
    #                                 "Symphonic Pop"         : [("Genre", "Orchestral"), ("Genre", "Pop")],          
    #                                 "Symphonic Rock"        : [("Genre", "Orchestral"), ("Genre", "Rock")],             
    #                                 "Classical Crossover"   : [("Genre", "Classical"), ("Genre", "Pop")],   
    #                                 "Dark Pop"              : [("Genre", "Pop"), ("Mood", "Dark")],     
    #                                 "Andalusian Folk"       : [("Genre", "Flamenco")],              
    #                                 "Anglo-American Folk"   : [("Genre", "Folk")],                  
    #                                 "British Isles Folk"    : [("Genre", "Folk")],                  
    #                                 "British Naval Folk"    : [("Genre", "Folk")],                  
    #                                 "Cornish Folk"          : [("Genre", "Folk")],          
    #                                 "Maritime Folk"         : [("Genre", "Folk")],          
    #                                 "Medieval Folk"         : [("Genre", "Folk"), ("Mood", "Medieval")],            
    #                                 "New Zealand Folk"      : [("Genre", "Folk")],              
    #                                 "Scots-Irish Folk"      : [("Genre", "Folk")],  
    #                                 "Russian Folk"          : [("Genre", "Folk")],
    #                                 "Scottish Folk"         : [("Genre", "Folk")],
    #                                 "Irish Folk"            : [("Genre", "Folk")],          
    #                                 "Brega"                 : [("Genre", "Latin"), ("Genre", "Pop")],   
    #                                 "Balearic"              : [("Genre", "Electronic")],        
    #                                 "Jumpstyle"             : [("Genre", "Electronic")],        
    #                                 "Glitch Hop"            : [("Genre", "Electronic")],            
    #                                 "Jump Blues"            : [("Genre", "Blues"), ("Genre", "Swing")],         
    #                                 "Outlaw Country"        : [("Genre", "Country")],               
    #                                 "Filk"                  : [("Genre", "Folk")],  
    #                                 "Post-Grunge"           : [("Genre", "Alternative Rock")],          
    #                                 "Romantic Era"          : [("Genre", "Classical")],     
    #                                 "Denpa"                 : [],   
    #                                 "J-Core"                : [],       
    #                                 "Lambada"               : [("Genre", "Latin")], 
    #                                 "English Folk"          : [("Genre", "Folk")],
    #                                 "French House"          : [("Genre", "House")],
    #                                 "French Pop"            : [("Genre", "Pop")],
    #                                 "French Rap"            : [("Genre", "Rap")],
    #                                 "Folk Metal"            : [("Genre", "Folk"), ("Genre", "Metal")],  
    #                                 "Folk Pop"              : [("Genre", "Folk"), ("Genre", "Pop")],
    #                                 "Meme"                  : [("Style", "Meme")],
    #                             },
    #                             }, exiftool_exe_path=exiftool_exe_path)
    
    #
    # with open('./all_possible_tags.json', 'r') as f:
    #     all_possible_tags = json.load(f)
    #     all_possible_tags['RealGenre'] = all_possible_tags['genre']
    #     del all_possible_tags['genre']
    #     deleteUndesiredTags(dir_path, exiftool_exe_path, possible_tags=all_possible_tags, tag_reorganisation='plex')
    
    
    
    