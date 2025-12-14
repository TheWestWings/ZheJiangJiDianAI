# LLM Providers 路由
import json
import sys
import os

# 添加services路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flask import request, jsonify
from routes import llm_providers_bp
from services.llm_providers import (
    get_factories,
    get_my_llms,
    set_api_key,
    add_llm,
    delete_llm,
    delete_factory,
    list_llms,
    SYSTEM_TENANT_ID
)


def success_response(data=None, message="success"):
    """成功响应"""
    return jsonify({"code": 0, "data": data, "message": message})


def error_response(message="error", code=1):
    """错误响应"""
    return jsonify({"code": code, "message": message})


@llm_providers_bp.route('/factories', methods=['GET'])
def factories():
    """获取所有可用的模型工厂列表"""
    try:
        data = get_factories()
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@llm_providers_bp.route('/my-llms', methods=['GET'])
def my_llms():
    """获取已配置的模型列表"""
    try:
        data = get_my_llms()
        return success_response(data)
    except Exception as e:
        return error_response(str(e))


@llm_providers_bp.route('/set-api-key', methods=['POST'])
def set_api_key_route():
    """
    设置API Key，批量导入该工厂下的所有模型
    
    请求体:
    {
        "llm_factory": "SILICONFLOW",
        "api_key": "sk-xxx",
        "base_url": "" (可选)
    }
    """
    try:
        data = request.get_json()
        
        llm_factory = data.get('llm_factory')
        api_key = data.get('api_key')
        base_url = data.get('base_url', '')
        
        if not llm_factory:
            return error_response("缺少参数: llm_factory")
        if not api_key:
            return error_response("缺少参数: api_key")
        
        success, message = set_api_key(llm_factory, api_key, base_url)
        
        if success:
            return success_response(True, message)
        else:
            return error_response(message)
    except Exception as e:
        return error_response(str(e))


@llm_providers_bp.route('/add-llm', methods=['POST'])
def add_llm_route():
    """
    添加单个自定义模型
    
    请求体:
    {
        "llm_factory": "Ollama",
        "llm_name": "llama2",
        "model_type": "chat",
        "api_key": "xxx",
        "api_base": "http://localhost:11434",
        "max_tokens": 4096
    }
    
    特殊工厂的api_key格式:
    - VolcEngine: {"ark_api_key": "xxx", "endpoint_id": "xxx"}
    - Tencent Hunyuan: {"hunyuan_sid": "xxx", "hunyuan_sk": "xxx"}
    - Bedrock: {"bedrock_ak": "xxx", "bedrock_sk": "xxx", "bedrock_region": "xxx"}
    - Google Cloud: {"google_project_id": "xxx", "google_region": "xxx", "google_service_account_key": "xxx"}
    - XunFei Spark (chat): spark_api_password
    - XunFei Spark (tts): {"spark_app_id": "xxx", "spark_api_secret": "xxx", "spark_api_key": "xxx"}
    - BaiduYiyan: {"yiyan_ak": "xxx", "yiyan_sk": "xxx"}
    - Fish Audio: {"fish_audio_ak": "xxx", "fish_audio_refid": "xxx"}
    - Azure OpenAI: {"api_key": "xxx", "api_version": "xxx"}
    """
    try:
        data = request.get_json()
        
        llm_factory = data.get('llm_factory')
        llm_name = data.get('llm_name')
        model_type = data.get('model_type')
        
        if not llm_factory:
            return error_response("缺少参数: llm_factory")
        if not llm_name:
            return error_response("缺少参数: llm_name")
        if not model_type:
            return error_response("缺少参数: model_type")
        
        # 处理特殊工厂的API Key
        api_key = data.get('api_key', 'x')
        
        if llm_factory == "VolcEngine":
            api_key = json.dumps({
                "ark_api_key": data.get("ark_api_key", ""),
                "endpoint_id": data.get("endpoint_id", "")
            })
        elif llm_factory == "Tencent Hunyuan":
            api_key = json.dumps({
                "hunyuan_sid": data.get("hunyuan_sid", ""),
                "hunyuan_sk": data.get("hunyuan_sk", "")
            })
        elif llm_factory == "Tencent Cloud":
            api_key = json.dumps({
                "tencent_cloud_sid": data.get("tencent_cloud_sid", ""),
                "tencent_cloud_sk": data.get("tencent_cloud_sk", "")
            })
        elif llm_factory == "Bedrock":
            api_key = json.dumps({
                "bedrock_ak": data.get("bedrock_ak", ""),
                "bedrock_sk": data.get("bedrock_sk", ""),
                "bedrock_region": data.get("bedrock_region", "")
            })
        elif llm_factory == "Google Cloud":
            api_key = json.dumps({
                "google_project_id": data.get("google_project_id", ""),
                "google_region": data.get("google_region", ""),
                "google_service_account_key": data.get("google_service_account_key", "")
            })
        elif llm_factory == "XunFei Spark":
            if model_type == "chat":
                api_key = data.get("spark_api_password", "")
            elif model_type == "tts":
                api_key = json.dumps({
                    "spark_app_id": data.get("spark_app_id", ""),
                    "spark_api_secret": data.get("spark_api_secret", ""),
                    "spark_api_key": data.get("spark_api_key", "")
                })
        elif llm_factory == "BaiduYiyan":
            api_key = json.dumps({
                "yiyan_ak": data.get("yiyan_ak", ""),
                "yiyan_sk": data.get("yiyan_sk", "")
            })
        elif llm_factory == "Fish Audio":
            api_key = json.dumps({
                "fish_audio_ak": data.get("fish_audio_ak", ""),
                "fish_audio_refid": data.get("fish_audio_refid", "")
            })
        elif llm_factory == "Azure-OpenAI":
            api_key = json.dumps({
                "api_key": data.get("api_key", ""),
                "api_version": data.get("api_version", "2024-02-01")
            })
        
        # 处理特殊的模型名称后缀
        if llm_factory == "LocalAI":
            llm_name += "___LocalAI"
        elif llm_factory == "HuggingFace":
            llm_name += "___HuggingFace"
        elif llm_factory == "OpenAI-API-Compatible":
            llm_name += "___OpenAI-API"
        elif llm_factory == "VLLM":
            llm_name += "___VLLM"
        
        api_base = data.get('api_base', '')
        max_tokens = data.get('max_tokens', 4096)
        
        success, message = add_llm(
            llm_factory, llm_name, model_type, 
            api_key, api_base, max_tokens
        )
        
        if success:
            return success_response(True, message)
        else:
            return error_response(message)
    except Exception as e:
        return error_response(str(e))


@llm_providers_bp.route('/delete-llm', methods=['POST'])
def delete_llm_route():
    """
    删除单个模型
    
    请求体:
    {
        "llm_factory": "Ollama",
        "llm_name": "llama2"
    }
    """
    try:
        data = request.get_json()
        
        llm_factory = data.get('llm_factory')
        llm_name = data.get('llm_name')
        
        if not llm_factory:
            return error_response("缺少参数: llm_factory")
        if not llm_name:
            return error_response("缺少参数: llm_name")
        
        success, message = delete_llm(llm_factory, llm_name)
        
        if success:
            return success_response(True, message)
        else:
            return error_response(message)
    except Exception as e:
        return error_response(str(e))


@llm_providers_bp.route('/delete-factory', methods=['POST'])
def delete_factory_route():
    """
    删除整个工厂的所有模型配置
    
    请求体:
    {
        "llm_factory": "SILICONFLOW"
    }
    """
    try:
        data = request.get_json()
        
        llm_factory = data.get('llm_factory')
        
        if not llm_factory:
            return error_response("缺少参数: llm_factory")
        
        success, message = delete_factory(llm_factory)
        
        if success:
            return success_response(True, message)
        else:
            return error_response(message)
    except Exception as e:
        return error_response(str(e))


@llm_providers_bp.route('/list', methods=['GET'])
def list_llms_route():
    """
    获取模型列表，包含可用性状态
    
    查询参数:
    - model_type: 可选，筛选模型类型
    """
    try:
        model_type = request.args.get('model_type')
        data = list_llms(model_type)
        return success_response(data)
    except Exception as e:
        return error_response(str(e))
