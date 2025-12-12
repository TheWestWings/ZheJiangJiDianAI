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
"""
角色管理相关数据库模型

包含以下表：
- Role: 角色表
- UserRole: 用户角色关联表（多对多）
- KnowledgebaseRole: 知识库角色权限表
- ModelRole: 模型角色权限表
"""

from peewee import CharField, TextField, IntegerField, CompositeKey

from api.db.db_models import DataBaseModel


class Role(DataBaseModel):
    """角色表"""
    id = CharField(max_length=32, primary_key=True)
    name = CharField(
        max_length=64,
        null=False,
        unique=True,
        help_text="角色名称",
        index=True
    )
    description = TextField(null=True, help_text="角色描述")
    is_default = IntegerField(
        default=0,
        help_text="是否默认角色 (0:否, 1:是)",
        index=True
    )
    status = CharField(
        max_length=1,
        null=True,
        help_text="状态 (0:禁用, 1:启用)",
        default="1",
        index=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "role"


class UserRole(DataBaseModel):
    """用户角色关联表（多对多）"""
    id = CharField(max_length=32, primary_key=True)
    user_id = CharField(
        max_length=32,
        null=False,
        help_text="用户ID",
        index=True
    )
    role_id = CharField(
        max_length=32,
        null=False,
        help_text="角色ID",
        index=True
    )

    class Meta:
        db_table = "user_role"
        indexes = (
            # 联合唯一索引
            (('user_id', 'role_id'), True),
        )


class KnowledgebaseRole(DataBaseModel):
    """知识库角色权限表"""
    id = CharField(max_length=32, primary_key=True)
    kb_id = CharField(
        max_length=32,
        null=False,
        help_text="知识库ID",
        index=True
    )
    role_id = CharField(
        max_length=32,
        null=False,
        help_text="角色ID",
        index=True
    )

    class Meta:
        db_table = "knowledgebase_role"
        indexes = (
            # 联合唯一索引
            (('kb_id', 'role_id'), True),
        )


class ModelRole(DataBaseModel):
    """模型角色权限表"""
    id = CharField(max_length=32, primary_key=True)
    tenant_id = CharField(
        max_length=32,
        null=False,
        help_text="租户ID",
        index=True
    )
    llm_factory = CharField(
        max_length=128,
        null=False,
        help_text="模型厂商",
        index=True
    )
    llm_name = CharField(
        max_length=128,
        null=False,
        help_text="模型名称",
        index=True
    )
    role_id = CharField(
        max_length=32,
        null=False,
        help_text="角色ID",
        index=True
    )

    class Meta:
        db_table = "model_role"
        indexes = (
            # 联合唯一索引
            (('tenant_id', 'llm_factory', 'llm_name', 'role_id'), True),
        )
