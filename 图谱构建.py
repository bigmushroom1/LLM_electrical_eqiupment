from py2neo import Graph, Node, Relationship
import pandas as pd

# 初始化连接到Neo4j
graph = Graph("bolt://localhost:7474", auth=("", ""))

# 清空数据库以防重复
graph.delete_all()

# 读取Excel数据
excel_file = "data.xlsx"
sheet_name = "Sheet2"
df = pd.read_excel(excel_file, sheet_name=sheet_name)

# 提取列名
columns = ["系统", "设备", "故障现象", "故障原因", "原因归类", "部件", "隐患等级"]

# 确保只保留所需列，避免多余数据干扰
df = df[columns]

# 去重处理，防止重复节点和关系
unique_nodes = {col: set(df[col].dropna().unique()) for col in columns}

# 创建节点
node_dict = {col: {} for col in columns}  # 用于存储节点对象以便快速查询
for col in columns:
    for value in unique_nodes[col]:
        node = Node(col, name=value)
        graph.create(node)
        node_dict[col][value] = node

# 创建关系
for _, row in df.iterrows():
    # 获取每行的值
    values = {col: row[col] for col in columns if not pd.isna(row[col])}

    # 创建 系统_TO_设备 关系
    if "系统" in values and "设备" in values:
        src_node = node_dict["系统"][values["系统"]]
        tgt_node = node_dict["设备"][values["设备"]]
        rel = Relationship.type("系统_TO_设备")
        graph.merge(rel(src_node, tgt_node))

    # 创建 故障现象 和 其他所有列之间的关系
    if "故障现象" in values:
        fault_node = node_dict["故障现象"][values["故障现象"]]
        for col in ["设备", "故障原因", "原因归类", "部件", "隐患等级"]:
            if col in values:
                other_node = node_dict[col][values[col]]
                rel = Relationship.type(f"故障现象_TO_{col}")
                graph.merge(rel(fault_node, other_node))

    # 创建 故障原因 和 原因归类 之间的关系
    if "故障原因" in values and "原因归类" in values:
        fault_cause_node = node_dict["故障原因"][values["故障原因"]]
        cause_type_node = node_dict["原因归类"][values["原因归类"]]
        rel = Relationship.type("故障原因_TO_原因归类")
        graph.merge(rel(fault_cause_node, cause_type_node))
