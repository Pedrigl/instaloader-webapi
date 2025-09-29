from fastapi import FastAPI, HTTPException, Response, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from instaloader import TwoFactorAuthRequiredException, BadCredentialsException

from instaloader.services.instagram_service import get_service_dep
import os
from instaloader.instaloader import get_default_session_filename

app = FastAPI()


# A simple in-memory way to keep a logged-in Instaloader for reuse across requests.
# In production you should persist the session securely and consider thread-safety.
def get_shared_loader(app: FastAPI):
    return getattr(app.state, 'loader', None)


@app.on_event('startup')
async def startup_load_saved_session():
    try:
        # We don't have DB session here; only load from config dir into service
        svc = get_service_dep() if not callable(get_service_dep) else None
        # get_service_dep is an async dependency for FastAPI; call the
        # underlying factory directly for startup actions.
        from instaloader.services.instagram_service import get_global_service

        username = await get_global_service().load_saved_session_if_any()
        if username:
            print(f'Loaded saved session for {username} from config dir')
    except Exception:
        # don't fail startup on session loading
        pass


class LoginBody(BaseModel):
    username: str
    password: str


@app.post('/login')
async def login(body: LoginBody, service=Depends(get_service_dep)):
    try:
        session = await service.login(body.username, body.password)
    except TwoFactorAuthRequiredException:
        # service.pending_2fa is set
        return {"status": "2fa_required", "detail": "Two-factor authentication required. Call /login/2fa with the code."}
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))

    # service stored loader/session internally

    # persist session in DB if available
    # (persistence handled by service)
    return {"status": "logged_in", "username": body.username}



class TwoFactorBody(BaseModel):
    code: str


@app.post('/login/2fa')
async def login_2fa(body: TwoFactorBody, service=Depends(get_service_dep)):
    try:
        session = await service.two_factor(body.code)
    except BadCredentialsException as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "logged_in", "username": service.get_username()}


@app.post('/logout')
async def logout(service=Depends(get_service_dep)):
    try:
        await service.logout()
    except Exception:
        raise HTTPException(status_code=400, detail='not logged in')
    return {"status": "logged_out"}


@app.get('/login/status')
def login_status(service=Depends(get_service_dep)):
    if not service.is_logged_in():
        return {"logged_in": False}
    return {"logged_in": True, "username": service.get_username()}


@app.get('/profile/{username}')
async def profile(username: str, service=Depends(get_service_dep)):
    try:
        data = await service.get_profile(username)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))



@app.get('/stories/{username}')
async def stories(username: str, service=Depends(get_service_dep)):
    try:
        items = await service.get_stories_for_user(username)
        for it in items:
            it.pop('get_bytes', None)
        return items
    except RuntimeError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/stories/{username}/media/{index}')
async def story_media(username: str, index: int = 1, service=Depends(get_service_dep)):
    try:
        content, mime = await service.get_story_media(username, index)
        return Response(content, media_type=mime)
    except IndexError:
        raise HTTPException(status_code=404, detail='story index out of range')
    except RuntimeError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get('/post/{shortcode}')
async def post(shortcode: str, service=Depends(get_service_dep)):
    try:
        data = await service.get_post(shortcode)
        return data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get('/post/{shortcode}/media/{index}')
async def post_media(shortcode: str, index: int = 1, service=Depends(get_service_dep)):
    try:
        content, mime = await service.get_post_media_bytes(shortcode, index)
        return Response(content, media_type=mime)
    except IndexError:
        raise HTTPException(status_code=404, detail='media index out of range')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
