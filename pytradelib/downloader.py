import asyncio

from aiohttp import ClientSession, ClientResponse, ClientResponseError

from .utils import chunk


async def bulk_download(urls, handle_resp, batch_size=8):
    if not isinstance(urls, (list, tuple)):
        urls = [urls]

    async def dl(session, url):
        async with session.get(url) as r:
            data, error = await handle_resp(r)
            if error:
                return url, error
            return url, data

    async def dl_all():
        results = []
        async with ClientSession() as session:
            for batch in chunk(urls, batch_size):
                tasks = [dl(session, url) for url in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=False)
                results.extend(batch_results)
        return results

    return await dl_all()
