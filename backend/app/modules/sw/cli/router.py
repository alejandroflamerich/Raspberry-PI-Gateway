import os
import logging
from fastapi import APIRouter, Depends, HTTPException
from typing import Any

from .models import CommandInfo, ExecuteRequest, ExecuteResponse
from . import registry
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get('/commands', response_model=list[CommandInfo])
async def list_commands(user: Any = Depends(get_current_user)):
    cmds = registry.list_commands()
    return cmds


@router.post('/execute', response_model=ExecuteResponse)
async def execute_cmd(payload: ExecuteRequest, user: Any = Depends(get_current_user)):
    try:
        res = registry.execute(payload.command, payload.args, context=user)
    except KeyError as ke:
        raise HTTPException(status_code=404, detail=str(ke))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception('execute failed')
        raise HTTPException(status_code=500, detail=str(e))

    return ExecuteResponse(ok=bool(res.get('ok')), output=res.get('output'), data=res.get('data'), logs=None, error=res.get('error'))
