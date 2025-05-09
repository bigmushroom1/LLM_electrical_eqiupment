import pandas as pd
from py2neo import Graph, Node, Relationship
graph = Graph('http://localhost:7474', auth=('', ''), name='neo4j')

# 读取Excel文件
file_path = 'FMEA.xlsx'
sheet_name = '舱门'

df = pd.read_excel(file_path, sheet_name=sheet_name)

# 选择需要的五列
data = df[['产品名称', '故障模式', '故障原因', '故障影响', '上一级故障影响']]

# 清空数据库（可选）
graph.delete_all()

# 创建节点和关系
for index, row in data.iterrows():
    product = Node("Product", name=row['产品名称'])
    failure_mode = Node("FailureMode", name=row['故障模式'])
    failure_cause = Node("FailureCause", name=row['故障原因'])
    failure_effect = Node("FailureEffect", name=row['故障影响'])
    higher_failure_effect = Node("HigherFailureEffect", name=row['上一级故障影响'])

    # 使用 merge 来避免重复插入
    graph.merge(product, "Product", "name")
    graph.merge(failure_mode, "FailureMode", "name")
    graph.merge(failure_cause, "FailureCause", "name")
    graph.merge(failure_effect, "FailureEffect", "name")
    graph.merge(higher_failure_effect, "HigherFailureEffect", "name")

    # 创建关系
    graph.create(Relationship(product, "HAS_MODE", failure_mode))
    graph.create(Relationship(failure_mode, "CAUSES", failure_cause))
    graph.create(Relationship(failure_mode, "IMPACTS", failure_effect))
    graph.create(Relationship(failure_effect, "LEADS_TO", higher_failure_effect))

# 其他代码可以根据需要继续扩展
