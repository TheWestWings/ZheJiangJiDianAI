#
#  Copyright 2024 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import logging
import json
import re
from datetime import datetime

from flask import request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, current_user, login_user, logout_user

from api.db.db_models import TenantLLM
from api.db.services.llm_service import TenantLLMService, LLMService
from api.utils.api_utils import (
    server_error_response,
    validate_request,
    get_data_error_result,
)
from api.utils import (
    get_uuid,
    get_format_time,
    decrypt,
    download_img,
    current_timestamp,
    datetime_format,
)
from api.db import UserTenantRole, FileType
from api import settings
from api.db.services.user_service import UserService, TenantService, UserTenantService
from api.db.services.file_service import FileService
from api.utils.api_utils import get_json_result, construct_response


@manager.route("/login", methods=["GET"])  # noqa: F821
def login():
    """
    Redirect to CAS login page.
    ---
    tags:
      - User
    responses:
      302:
        description: Redirect to CAS authentication page.
    """
    # 构建 CAS 授权 URL
    cas_url = (
        f"{settings.CAS_CONFIG.get('authorize_url')}?"
        f"response_type=code&"
        f"client_id={settings.CAS_CONFIG.get('client_id')}&"
        f"redirect_uri={settings.CAS_CONFIG.get('redirect_uri')}"
    )
    return redirect(cas_url)


@manager.route("/cas_login_url", methods=["GET"])  # noqa: F821
def get_cas_login_url():
    """
    Get CAS login URL for frontend redirect.
    ---
    tags:
      - User
    responses:
      200:
        description: CAS login URL.
        schema:
          type: object
          properties:
            url:
              type: string
              description: CAS authorization URL.
    """
    cas_url = (
        f"{settings.CAS_CONFIG.get('authorize_url')}?"
        f"response_type=code&"
        f"client_id={settings.CAS_CONFIG.get('client_id')}&"
        f"redirect_uri={settings.CAS_CONFIG.get('redirect_uri')}"
    )
    return get_json_result(data={"url": cas_url})


@manager.route("/cas_callback", methods=["GET"])  # noqa: F821
def cas_callback():
    """
    ZIME CAS OAuth callback endpoint.
    统一身份认证回调接口，用于处理 CAS 登录后的回调
    ---
    tags:
      - OAuth
    parameters:
      - in: query
        name: code
        type: string
        required: true
        description: Authorization code from ZIME CAS.
      - in: query
        name: state
        type: string
        required: false
        description: Optional state parameter for CSRF protection.
    responses:
      302:
        description: Redirect to homepage with auth token or error.
    """
    import requests

    code = request.args.get("code")
    if not code:
        return redirect("/?error=Missing authorization code")

    # Step 2: 使用 code 换取 access_token
    try:
        token_response = requests.get(
            settings.CAS_CONFIG.get("access_token_url"),
            params={
                "client_id": settings.CAS_CONFIG.get("client_id"),
                "client_secret": settings.CAS_CONFIG.get("client_secret"),
                "code": code,
                "redirect_uri": settings.CAS_CONFIG.get("redirect_uri"),
            },
            timeout=10
        )
        token_data = token_response.json()

        if "errorcode" in token_data:
            error_msg = token_data.get("errormsg", "Token exchange failed")
            logging.error(f"CAS token exchange failed: {error_msg}")
            return redirect(f"/?error={error_msg}")

        access_token = token_data.get("access_token")
        if not access_token:
            return redirect("/?error=Failed to get access token")

    except Exception as e:
        logging.exception("CAS token exchange failed")
        return redirect("/?error=Token exchange error")

    # Step 3: 使用 access_token 获取用户信息
    try:
        user_info = get_cas_user_info(access_token)
    except Exception as e:
        logging.exception("CAS user info fetch failed")
        return redirect("/?error=User info fetch error")

    # 用户信息映射
    user_code = user_info.get("CODE") or user_info.get("id")
    user_name = user_info.get("XM") or user_code
    
    # 生成邮箱（使用工号/学号@zime.edu.cn格式）
    email_address = f"{user_code}@zime.edu.cn"

    users = UserService.query(email=email_address)
    user_id = get_uuid()

    if not users:
        # 新用户自动注册
        try:
            users = user_register(
                user_id,
                {
                    "access_token": get_uuid(),
                    "email": email_address,
                    "avatar": "",  # ZIME CAS 暂无头像接口
                    "nickname": user_name,
                    "login_channel": "cas",
                    "last_login_time": get_format_time(),
                    "is_superuser": False,
                },
            )
            if not users:
                raise Exception(f"Fail to register {email_address}.")
            if len(users) > 1:
                raise Exception(f"Same email: {email_address} exists!")

            # 登录用户
            user = users[0]
            login_user(user)
            logging.info(f"New user registered via CAS: {email_address}")
            return redirect(f"/?auth={user.get_id()}")
        except Exception as e:
            rollback_user_registration(user_id)
            logging.exception(e)
            return redirect(f"/?error={str(e)}")

    # 已注册用户直接登录
    user = users[0]
    user.access_token = get_uuid()
    login_user(user)
    user.save()
    logging.info(f"User logged in via CAS: {email_address}")
    return redirect(f"/?auth={user.get_id()}")


def get_cas_user_info(access_token):
    """
    从 ZIME CAS 获取用户信息
    
    返回示例:
    {
        "id": "testuser",
        "CODE": "testuser",  # 工号/学号
        "XM": "testuser",    # 姓名
        "DWPF": "XX",        # 部门
    }
    """
    import requests

    response = requests.get(
        settings.CAS_CONFIG.get("profile_url"),
        params={"access_token": access_token},
        timeout=10
    )

    data = response.json()
    logging.info(f"CAS profile response: {data}")

    if "errorcode" in data:
        raise Exception(f"CAS profile error: {data.get('errormsg')}")

    # 解析 attributes - 可能是 dict 或 list
    attributes = data.get("attributes", {})
    
    # 如果 attributes 是列表，转换为字典
    if isinstance(attributes, list):
        # 列表格式可能是 [{"CODE": "xxx"}, {"XM": "yyy"}] 或其他格式
        attrs_dict = {}
        for item in attributes:
            if isinstance(item, dict):
                attrs_dict.update(item)
            elif isinstance(item, str):
                # 可能是 "KEY=VALUE" 格式
                if "=" in item:
                    key, value = item.split("=", 1)
                    attrs_dict[key] = value
        attributes = attrs_dict
    elif not isinstance(attributes, dict):
        attributes = {}

    # 扁平化用户信息
    user_info = {
        "id": data.get("id"),
        "CODE": attributes.get("CODE") if isinstance(attributes, dict) else None,
        "XM": attributes.get("XM") if isinstance(attributes, dict) else None,
        "DWPF": attributes.get("DWPF") if isinstance(attributes, dict) else None,
    }

    logging.info(f"Parsed user_info: {user_info}")
    return user_info


@manager.route("/logout", methods=["GET"])  # noqa: F821
@login_required
def log_out():
    """
    User logout endpoint - redirects to CAS logout.
    ---
    tags:
      - User
    security:
      - ApiKeyAuth: []
    responses:
      302:
        description: Redirect to CAS logout page.
    """
    # 清除本地会话
    current_user.access_token = ""
    current_user.save()
    logout_user()
    
    # 构建 CAS 退出 URL
    # CAS 退出后会重定向回首页
    cas_logout_url = "https://account.zime.edu.cn/cas/logout"
    redirect_after_logout = settings.CAS_CONFIG.get("redirect_uri", "").replace("/v1/user/cas_callback", "")
    
    if redirect_after_logout:
        cas_logout_url = f"{cas_logout_url}?service={redirect_after_logout}"
    
    return redirect(cas_logout_url)


@manager.route("/setting", methods=["POST"])  # noqa: F821
@login_required
def setting_user():
    """
    Update user settings.
    ---
    tags:
      - User
    security:
      - ApiKeyAuth: []
    parameters:
      - in: body
        name: body
        description: User settings to update.
        required: true
        schema:
          type: object
          properties:
            nickname:
              type: string
              description: New nickname.
            email:
              type: string
              description: New email.
    responses:
      200:
        description: Settings updated successfully.
        schema:
          type: object
    """
    update_dict = {}
    request_data = request.json
    if request_data.get("password"):
        new_password = request_data.get("new_password")
        if not check_password_hash(
                current_user.password, decrypt(request_data["password"])
        ):
            return get_json_result(
                data=False,
                code=settings.RetCode.AUTHENTICATION_ERROR,
                message="Password error!",
            )

        if new_password:
            update_dict["password"] = generate_password_hash(decrypt(new_password))

    for k in request_data.keys():
        if k in [
            "password",
            "new_password",
            "email",
            "status",
            "is_superuser",
            "login_channel",
            "is_anonymous",
            "is_active",
            "is_authenticated",
            "last_login_time",
        ]:
            continue
        update_dict[k] = request_data[k]

    try:
        UserService.update_by_id(current_user.id, update_dict)
        return get_json_result(data=True)
    except Exception as e:
        logging.exception(e)
        return get_json_result(
            data=False, message="Update failure!", code=settings.RetCode.EXCEPTION_ERROR
        )


@manager.route("/info", methods=["GET"])  # noqa: F821
@login_required
def user_profile():
    """
    Get user profile information.
    ---
    tags:
      - User
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: User profile retrieved successfully.
        schema:
          type: object
          properties:
            id:
              type: string
              description: User ID.
            nickname:
              type: string
              description: User nickname.
            email:
              type: string
              description: User email.
    """
    return get_json_result(data=current_user.to_dict())


def rollback_user_registration(user_id):
    try:
        UserService.delete_by_id(user_id)
    except Exception:
        pass
    try:
        TenantService.delete_by_id(user_id)
    except Exception:
        pass
    try:
        u = UserTenantService.query(tenant_id=user_id)
        if u:
            UserTenantService.delete_by_id(u[0].id)
    except Exception:
        pass
    try:
        TenantLLM.delete().where(TenantLLM.tenant_id == user_id).execute()
    except Exception:
        pass


def user_register(user_id, user):
    user["id"] = user_id
    tenant = {
        "id": user_id,
        "name": user["nickname"] + "‘s Kingdom",
        "llm_id": settings.CHAT_MDL,
        "embd_id": settings.EMBEDDING_MDL,
        "asr_id": settings.ASR_MDL,
        "parser_ids": settings.PARSERS,
        "img2txt_id": settings.IMAGE2TEXT_MDL,
        "rerank_id": settings.RERANK_MDL,
    }
    usr_tenant = {
        "tenant_id": user_id,
        "user_id": user_id,
        "invited_by": user_id,
        "role": UserTenantRole.OWNER,
    }
    file_id = get_uuid()
    file = {
        "id": file_id,
        "parent_id": file_id,
        "tenant_id": user_id,
        "created_by": user_id,
        "name": "/",
        "type": FileType.FOLDER.value,
        "size": 0,
        "location": "",
    }
    tenant_llm = []
    for llm in LLMService.query(fid=settings.LLM_FACTORY):
        tenant_llm.append(
            {
                "tenant_id": user_id,
                "llm_factory": settings.LLM_FACTORY,
                "llm_name": llm.llm_name,
                "model_type": llm.model_type,
                "api_key": settings.API_KEY,
                "api_base": settings.LLM_BASE_URL,
                "max_tokens": llm.max_tokens if llm.max_tokens else 8192
            }
        )

    if not UserService.save(**user):
        return
    TenantService.insert(**tenant)
    UserTenantService.insert(**usr_tenant)
    TenantLLMService.insert_many(tenant_llm)
    FileService.insert(file)
    return UserService.query(email=user["email"])



# 注册功能已禁用 - 所有用户通过 CAS 统一身份认证自动注册




@manager.route("/tenant_info", methods=["GET"])  # noqa: F821
@login_required
def tenant_info():
    """
    Get tenant information.
    ---
    tags:
      - Tenant
    security:
      - ApiKeyAuth: []
    responses:
      200:
        description: Tenant information retrieved successfully.
        schema:
          type: object
          properties:
            tenant_id:
              type: string
              description: Tenant ID.
            name:
              type: string
              description: Tenant name.
            llm_id:
              type: string
              description: LLM ID.
            embd_id:
              type: string
              description: Embedding model ID.
    """
    try:
        tenants = TenantService.get_info_by(current_user.id)
        if not tenants:
            return get_data_error_result(message="Tenant not found!")
        return get_json_result(data=tenants[0])
    except Exception as e:
        return server_error_response(e)


@manager.route("/set_tenant_info", methods=["POST"])  # noqa: F821
@login_required
@validate_request("tenant_id", "asr_id", "embd_id", "img2txt_id", "llm_id")
def set_tenant_info():
    """
    Update tenant information.
    ---
    tags:
      - Tenant
    security:
      - ApiKeyAuth: []
    parameters:
      - in: body
        name: body
        description: Tenant information to update.
        required: true
        schema:
          type: object
          properties:
            tenant_id:
              type: string
              description: Tenant ID.
            llm_id:
              type: string
              description: LLM ID.
            embd_id:
              type: string
              description: Embedding model ID.
            asr_id:
              type: string
              description: ASR model ID.
            img2txt_id:
              type: string
              description: Image to Text model ID.
    responses:
      200:
        description: Tenant information updated successfully.
        schema:
          type: object
    """
    req = request.json
    try:
        tid = req.pop("tenant_id")
        TenantService.update_by_id(tid, req)
        return get_json_result(data=True)
    except Exception as e:
        return server_error_response(e)
