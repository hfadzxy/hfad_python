# 导入mysqldb 代替sqlite3 数据库
from pymysql import install_as_MySQLdb

# 调用函数
install_as_MySQLdb()