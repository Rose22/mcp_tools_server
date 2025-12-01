import utils

import os
import datetime
import requests
import asyncio
import aiohttp
import urllib
import json

async def process_webpage(html):
    # uses beautifulsoup to scrape a webpage

    output = {}

    import re
    from bs4 import BeautifulSoup

    soup = await asyncio.to_thread(BeautifulSoup, html, "html.parser")

    # we can usually get plenty of information from just the title, headers and paragraphs of a page!
    try:
        output["title"] = soup.find("title").get_text().strip()
    except AttributeError:
        # no title found
        pass

    output["headers"] = []
    for header in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        output["headers"].append(header.get_text().strip())
    if not output["headers"]:
        del output["headers"]

    output["paragraphs"] = []
    for para in soup.find_all("p"):
        output["paragraphs"].append(para.get_text().strip())
    if not output["paragraphs"]:
        del output["paragraphs"]

    output["images"] = []
    for image in soup.find_all("img"):
        if image.get("alt"):
            output["images"].append(image.get("alt"))

    if not output["images"]:
        del output["images"]

    # remove duplicates
    for category in list(output.keys()):
        if category == "title":
            continue

        output[category] = utils.remove_duplicates(output[category])

    # but not always...
    if "headers" not in output.keys() and "paragraphs" not in output.keys():
        # if nothing was found, first, fall back on common CSS classes
        output["classes"] = {}
        for class_name in (
            "content",
            "description",
            "title",
            "text",
            "article",
        ):
            output["classes"][class_name] = []
            for element in soup.find_all(
                class_=re.compile(rf"\b{class_name}\b")
            ):
                if element.text != "":
                    output["classes"][class_name].append(element.text)
            # also get elements by id
            for element in soup.find_all(id=re.compile(rf"\b{class_name}\b")):
                if element.text != "":
                    output["classes"][class_name].append(element.text)

            if not output["classes"][class_name]:
                # no data found for the class? just delete it from the response
                del output["classes"][class_name]
                continue

            # remove duplicates
            output["classes"][class_name] = utils.remove_duplicates(
                output["classes"][class_name]
            )

        if not output["classes"]:
            # still nothing?
            # then fall back on links if nothing could be extracted from the other html elements.
            # this is a last resort because it tends to be a lot of data to process

            del output["classes"]

            output["urls"] = []
            for a in soup.find_all("a", href=True):
                output["urls"].append(a["href"])

            # remove duplicate links
            output["urls"] = utils.remove_duplicates(output["urls"])

            if not output["urls"]:
                # alright, theres no saving this one. at least we have a title!
                del output["urls"]

                output["message"] = (
                    "nothing could be scraped from the page!"
                )

    return output

async def process_domains(domain, url, purpose, memory):
    if "youtube" in domain and "watch" in url or "youtu.be" in domain:
        # this is a youtube link. try and get the transcript!
        import youtube_transcript_api

        err = None

        # get video transcript using a python module
        ytt_api = youtube_transcript_api.YouTubeTranscriptApi()

        parsed = urllib.parse.urlparse(url)
        # how to get the video id depends on if it's youtube or youtu.be
        if "youtube" in domain:
            query = urllib.parse.parse_qs(parsed.query)
            video_id = query.get("v", [None])[0]
            if not video_id:
                err = "No video id found in URL"
        elif domain == "youtu.be":
            video_id = parsed.path.lstrip("/")

        try:
            transcript_obj = ytt_api.fetch(video_id)
        except:
            # that likely means a transcript wasn't available in the preferred language.
            # so fall back on the first one available:
            try:
                transcript_obj_list = list(ytt_api.list(video_id))
                transcript_obj = transcript_obj_list[0].fetch()
            except Exception as e:
                err = f"couldn't find subtitles. tell the user the title of the video!"

        # get video title using beautifulsoup
        from bs4 import BeautifulSoup

        html = await utils.http_request(url)
        soup = await asyncio.to_thread(BeautifulSoup, html, "html.parser")

        title = soup.find("title").get_text().strip()

        transcript_dict = {"type": "youtube", "title": title}

        if not err:
            transcript = []
            for snippet in transcript_obj:
                transcript.append(snippet.text)
            transcript_text = " ".join(transcript)

            transcript_dict["transcript"] = {
                "language": f"({transcript_obj.language_code}) {transcript_obj.language}",
                "auto_generated": transcript_obj.is_generated,
                "content": transcript_text,
                "words": len(transcript_text.split(" ")),
            }
        else:
            transcript_dict["error"] = err

        return transcript_dict

async def process_text(file_content):
    return file_content.decode(errors="replace")

async def process_image(file_content):
    import base64

    return base64.b64encode(file_content).decode("utf-8")

async def process_xml(file_content):
    import xmltodict

    return xmltodict.parse(file_content.decode(errors="replace"))

async def process_yaml(file_content):
    import yaml
    import json

    try:
        return json.dumps(
            yaml.safe_load(file_content.decode(errors="replace")),
            indent=2,
        )
    except yaml.YAMLError as e:
        return f"YAML Error: {e}"

async def process_csv(file_content):
    from io import StringIO
    import csv

    output = []
    for row in csv.reader(StringIO(file_content.decode(errors="replace"))):
        output.append(list(row))

    return output

async def process_pdf(file_content):
    from io import BytesIO
    import pypdf

    pdfreader = pypdf.PdfReader(BytesIO(file_content))
    pages_text = []
    for page in pdfreader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)

    return pages_text

async def process_audio(file_content):
    from io import BytesIO
    import tinytag

    tagreader = tinytag.TinyTag.get(file_obj=BytesIO(file_content))
    return tagreader.as_dict()

async def process_video(file_content):
    import moviepy
    import tempfile

    # moviepy is stubborn and absolutely insists on a file name, not a file object
    # so let's write it to a file i guess...
    tmp_path = ""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name

    clip = None
    try:
        clip = moviepy.VideoFileClip(tmp_path)

        output = {
            "duration": clip.duration,
            "fps": clip.fps,
            "width": clip.w,
            "height": clip.h,
            "has_audio": clip.audio is not None,
            "audio_channels": clip.audio.nchannels if clip.audio else None,
            "audio_fps": clip.audio.fps if clip.audio else None,
            "misc": getattr(clip.reader, "infos", None),
        }
    finally:
        if clip:
            clip.close()
        os.remove(tmp_path)

    return output

async def process_zip(file_content):
    from io import BytesIO
    import zipfile

    zip = zipfile.ZipFile(BytesIO(file_content))
    return zip.namelist()

async def process_rar(file_content):
    from io import BytesIO
    import rarfile

    rar = rarfile.RarFile(BytesIO(file_content))
    output = []
    for f in rar.infolist():
        output.append(f.filename)

    return output

async def process_tar(file_content):
    from io import BytesIO
    import tarfile

    tar = tarfile.open(fileobj=BytesIO(file_content))

    output = []
    for f in tar.getmembers():
        output.append(f.name)

    return output

async def process_exe(file_content):
    return "user submitted an executable file. use a tool call that searches the web to fetch further information."

# ---------------------
# --- MAIN FUNCTION ---
# ---------------------
async def read_file_or_url(
    path: str,
    purpose: str,
    memory: str,
    multi: bool = False,
):
    """
    processes any file or url user may have provided.
    use the "purpose" argument to describe the purpose of this request.
    use the "memory" argument for details that must be remembered by the LLM after parsing all the data, such as details about the user.

    will process:
    - websites
    - html
    - xml
    - markdown
    - source code
    - scripts
    - json
    - yaml
    - ini
    - csv
    - logs
    - images
    - music
    - videos
    - PDFs
    - documents
    - archive files such as zip and rar
    - youtube videos
    - executables
    """

    utils.console_log(f"processing path: {path}")

    output = {}

    # check if path is file or url
    url_parser = urllib.parse.urlparse(path)
    if url_parser.scheme != "":
        # parse the URL

        domain = url_parser.netloc
        file_name = url_parser.path.split("/")[-1]
        file_name_split = file_name.split(".")
        file_type = file_name_split[-1].lower() if len(file_name_split) > 1 else None

        # first, process any special domains, such as youtube
        output = await process_domains(domain, path, purpose, memory)
        if output:
            return utils.result(output)

        # then if that didn't do anything, switch to Processing based on file type

        # get the content of whatever file is at the url
        file_content = await utils.http_request(path)
    else:
        # not a url
        path = os.path.expanduser(path)
        if os.path.exists(path):
            if os.path.isfile(path):
                # this is a file
                utils.console_log("reading local file..")

                file_name, file_type = os.path.splitext(os.path.basename(path))
                file_type = file_type.lstrip('.')
                with open(path, 'rb') as f:
                    file_content = f.read()
            elif os.path.isdir(path):
                return utils.list_dir(path)
        else:
            # file not found!
            return utils.result(None, "no such file or directory")

    import hashlib

    filetype_map = {
        ("htm", "html", "xhtml", "php", "asp"): process_webpage,
        (
            "asm",
            "bas",
            "bat",
            "c",
            "cc",
            "cfg",
            "cgi",
            "clj",
            "conf",
            "cpp",
            "css",
            "dart",
            "diff",
            "elm",
            "erl",
            "ex",
            "fs",
            "go",
            "hs",
            "ini",
            "java",
            "jl",
            "js",
            "json",
            "kt",
            "lisp",
            "log",
            "lua",
            "m",
            "md",
            "ml",
            "php",
            "pl",
            "ps1",
            "psm1",
            "patch",
            "py",
            "r",
            "rb",
            "rs",
            "s1",
            "scala",
            "scm",
            "sh",
            "sql",
            "swift",
            "ts",
            "txt",
            "toml",
            "tsx",
            "vim",
            "zsh",
        ): process_text,
        (
            "jpg",
            "jpeg",
            "png",
            "gif",
            "bmp",
            "svg",
            "tiff",
            "webp",
            "ico",
            "raw",
            "heic",
            "eps",
            "ai",
        ): process_image,
        ("mp3", "m4a", "ogg", "flac", "wma", "aiff", "wav", "aac"): process_audio,
        (
            "mp4",
            "mkv",
            "mov",
            "avi",
            "wmv",
            "mpeg",
            "mpg",
            "m4v",
        ): process_video,
        ("tar", "gz", "tgz"): process_tar,
        (
            "bin",
            "exe",
            "dll",
            "elf",
            "msi",
            "com",
            "cmd",
            "msp",
            "so",
            "a",
            "la",
            "bin",
            "dmg",
            "app",
            "appimage",
            "flatpak",
            "x64",
            "x86",
            "arm",
            "jar",
            "apk",
            "deb",
            "rpm",
        ): process_exe,
        ("zip",): process_zip,
        ("rar",): process_rar,
        ("xml",): process_xml,
        ("yaml",): process_yaml,
        ("csv",): process_csv,
        ("pdf",): process_pdf,
    }

    processor = None
    for exts, fetched_processor in filetype_map.items():
        if file_type in exts:
            processor = fetched_processor
            break

    if processor:
        utils.console_log("processing using "+processor.__name__)
        output = await processor(file_content)
    elif not file_type:
        # for now, we assume it's a website.
        # TODO: add mime type checking
        utils.console_log("processing using process_webpage")
        output = await process_webpage(file_content)

        file_type = "website"
    else:
        # some unknown file format
        # add MIME type-based Processing later
        utils.console_log("could not find valid processor!")

        output = (
            "unsupported file format! you have to use another tool to process this."
        )

    result = {
        "path": path,
        "filename": file_name,
        "type": file_type,
        "size": len(file_content),
        "checksum": hashlib.sha256(file_content).hexdigest(),
        "data": output,
    }

    if not multi:
        result["ai_instructions"] = {
            "important_details": memory,
            "purpose_of_request": purpose,
        }
        utils.console_log("done processing")
        return utils.result(result)
    else:
        return result

async def read_multiple_files_or_urls(
    paths: list,
    purpose: str,
    memory: str
):
    """
    processes multiple files or url's in sequence. can process the exact same data types as read_file_or_url.
    use this instead of read_file_or_url if user provided multiple files or url's!

    use the "purpose" argument to describe the purpose of this request.
    use the "memory" argument for details that must be remembered by the LLM after parsing all the data, such as details about the user.
    """

    output = []

    utils.console_log("processing multiple files asynchronously..")

    # limit to 4 threads at once
    semaphore = asyncio.Semaphore(4)

    async def handle_one(path, i):
        async with semaphore:
            try:
                # for if the AI adds the url as a dict for some reason. it often does that!
                path = path["path"]
            except:
                pass

            try:
                utils.console_log(f"thread {i}: launching..")
                result = await read_file_or_url(
                    path, purpose, memory, multi=True
                )
                utils.console_log(f"thread {i}: finished!")
                return result
            except Exception as e:
                return [f"ERROR Processing path {path}: {e}"]

    tasks = [handle_one(path, i) for i, path in enumerate(paths)]
    output = await asyncio.gather(*tasks)

    return {
        "results": output,
        "ai_instructions": {
            "important_details": memory,
            "purpose_of_request": f"{purpose}. Include links to all sources.",
        },
    }

def register_mcp(mcp):
    mcp.tool(read_file_or_url)
    mcp.tool(read_multiple_files_or_urls)
