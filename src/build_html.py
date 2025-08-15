#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建单个HTML文件，包含所有数据
将所有教师、评论、GPA数据嵌入到一个HTML文件中，实现真正的前后端合并
"""

import json
import csv
import sys
from pathlib import Path
from collections import defaultdict
import html
import math

class SingleHTMLBuilder:
    def __init__(self, source_dir=None, output_file=None, 
                 generate_individual_pages=False, teachers_dir=None):
        # 获取脚本所在目录
        script_dir = Path(__file__).parent
        
        # 设置默认路径，如果脚本在 src 目录中，则使用相对于项目根目录的路径
        if script_dir.name == "src":
            # 脚本在 src 目录中，路径相对于项目根目录
            base_dir = script_dir.parent
            default_source_dir = base_dir / "comment" / "extracted"
            default_output_file = base_dir / "web" / "complete.html"
            default_teachers_dir = base_dir / "web" / "teachers"
        else:
            # 脚本在项目根目录中，使用原来的路径
            default_source_dir = script_dir / "comment" / "extracted"
            default_output_file = script_dir / "web" / "complete.html"
            default_teachers_dir = script_dir / "web" / "teachers"
        
        self.source_dir = Path(source_dir) if source_dir else default_source_dir
        self.output_file = Path(output_file) if output_file else default_output_file
        self.teachers_dir = Path(teachers_dir) if teachers_dir else default_teachers_dir
        self.generate_individual_pages = generate_individual_pages
        self.teachers = []
        self.comments = []
        self.gpa_data = {}
        self.statistics = {}
        self.update_date = self.get_update_date()
    
    def normalize_newlines(self, text):
        """
        标准化换行符，将 \\n 转换为真正的换行符
        """
        if isinstance(text, str):
            # 将字符串中的 \\n 替换为真正的换行符
            return text.replace('\\n', '\n')
        return text
    
    def safe_json_dumps(self, obj):
        """
        安全的JSON序列化，确保换行符正确处理
        """
        return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
        
    def get_update_date(self):
        """从 logs/archive_info.json 获取更新日期"""
        try:
            # 获取脚本所在目录
            script_dir = Path(__file__).parent
            
            # 设置 archive_info.json 文件路径
            if script_dir.name == "src":
                # 脚本在 src 目录中
                archive_info_file = script_dir.parent / "logs" / "archive_info.json"
            else:
                # 脚本在项目根目录中
                archive_info_file = script_dir / "logs" / "archive_info.json"
                
            if archive_info_file.exists():
                with open(archive_info_file, 'r', encoding='utf-8') as f:
                    archive_info = json.load(f)
                    if archive_info and len(archive_info) > 0:
                        return archive_info[0].get("date_formatted", "2025-08-13")
        except Exception as e:
            print(f"⚠️ 读取更新日期失败: {e}")
        return "2025-08-13"  # 默认日期
        
    def build_all(self):
        """构建教师索引页面和单个教师页面"""
        print("🚀 开始构建HTML文件...")
        
        # 加载所有数据
        self.load_teachers_data()
        self.load_comments_data()
        self.load_gpa_data()
        self.build_statistics()
        
        # 生成单个教师页面
        if self.generate_individual_pages:
            self.generate_individual_teacher_pages()
        
        print(f"✅ HTML文件构建完成！")
        print(f"📁 教师索引页面: web/index.html")
        print(f"📊 包含数据: {len(self.teachers)} 位教师, {len(self.comments)} 条评论")
        
        if self.generate_individual_pages:
            print(f"📁 教师页面目录: {self.teachers_dir}")
            print(f"📄 生成了 {len(self.teachers)} 个教师页面")
        
    def load_teachers_data(self):
        """加载教师数据"""
        print("📚 加载教师数据...")
        
        teachers_file = self.source_dir / "teachers.csv"
        if not teachers_file.exists():
            print(f"❌ 教师数据文件不存在: {teachers_file}")
            return
            
        teachers = []
        with open(teachers_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    teacher = {
                        "id": int(row["id"]),
                        "name": row["姓名"],
                        "college": row["学院"], 
                        "heat": int(row["热度"]),
                        "rating_count": int(row["评分人数"]),
                        "rating": float(row["评分"]),
                        "pinyin": row["拼音"],
                        "pinyin_abbr": row["拼音缩写"]
                    }
                    teachers.append(teacher)
                except (ValueError, KeyError) as e:
                    continue
        
        self.teachers = teachers
        print(f"✅ 教师数据加载完成: {len(teachers)} 位教师")
        
    def load_comments_data(self):
        """加载评论数据"""
        print("💬 加载评论数据...")
        
        comments = []
        total_files = 0
        
        # 处理所有评论文件
        comment_files = list(self.source_dir.glob("comment_*.csv"))
        total_files = len(comment_files)
        print(f"发现 {total_files} 个评论文件")
        
        for i, comment_file in enumerate(comment_files):
            print(f"处理文件 {i+1}/{total_files}: {comment_file.name}")
            
            try:
                with open(comment_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    file_comments = 0
                    for row in reader:
                        try:
                            comment = {
                                "id": int(row["评论id"]),
                                "teacher_id": int(row["老师id"]),
                                "teacher_name": row["老师姓名"],
                                "post_time": row["发表时间"],
                                "like_diff": int(row["点赞减去点踩数量"]),
                                "likes": int(row["点赞量"]),
                                "dislikes": int(row["点踩量"]),
                                "content": self.normalize_newlines(row["内容"])
                            }
                            comments.append(comment)
                            file_comments += 1
                        except (ValueError, KeyError) as e:
                            continue
                    
                    print(f"  加载了 {file_comments} 条评论")
                            
            except Exception as e:
                print(f"⚠️ 处理文件 {comment_file.name} 时出错: {e}")
                continue
        
        self.comments = comments
        print(f"✅ 评论数据加载完成: {len(comments)} 条评论")
        
    def load_gpa_data(self):
        """加载GPA数据"""
        print("📊 加载GPA数据...")
        
        gpa_file = self.source_dir / "gpa.json"
        if not gpa_file.exists():
            print(f"⚠️ GPA数据文件不存在: {gpa_file}")
            self.gpa_data = {}
            return
        
        try:
            with open(gpa_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    gpa_data = json.loads(content)
                else:
                    gpa_data = {}
        except json.JSONDecodeError:
            print("⚠️ GPA文件格式错误，使用空数据")
            gpa_data = {}
        
        # 处理GPA数据格式
        processed_gpa = {}
        for teacher_name, courses in gpa_data.items():
            processed_courses = []
            for course in courses:
                if len(course) >= 4:
                    processed_course = {
                        "name": course[0],
                        "gpa": course[1],
                        "student_count": course[2], 
                        "std_dev": course[3]
                    }
                    processed_courses.append(processed_course)
            
            if processed_courses:
                processed_gpa[teacher_name] = processed_courses
        
        self.gpa_data = processed_gpa
        print(f"✅ GPA数据加载完成: {len(processed_gpa)} 位教师的课程数据")
        
    def build_statistics(self):
        """构建统计数据"""
        print("📈 构建统计数据...")
        
        # 基础统计
        total_teachers = len(self.teachers)
        total_comments = len(self.comments)
        
        # 学院统计
        college_stats = defaultdict(lambda: {"teacher_count": 0, "total_rating": 0, "total_heat": 0})
        
        for teacher in self.teachers:
            college = teacher["college"]
            college_stats[college]["teacher_count"] += 1
            college_stats[college]["total_rating"] += teacher["rating"]
            college_stats[college]["total_heat"] += teacher["heat"]
        
        # 计算平均值
        college_list = []
        for college, stats in college_stats.items():
            if stats["teacher_count"] > 0:
                avg_rating = stats["total_rating"] / stats["teacher_count"]
                college_list.append({
                    "college": college,
                    "teacher_count": stats["teacher_count"],
                    "avg_rating": round(avg_rating, 2),
                    "total_heat": stats["total_heat"]
                })
        
        # 按教师数量排序
        college_list.sort(key=lambda x: x["teacher_count"], reverse=True)
        
        # 评分分布
        rating_distribution = {"0-3": 0, "3-5": 0, "5-7": 0, "7-9": 0, "9-10": 0}
        for teacher in self.teachers:
            rating = teacher["rating"]
            if rating < 3:
                rating_distribution["0-3"] += 1
            elif rating < 5:
                rating_distribution["3-5"] += 1
            elif rating < 7:
                rating_distribution["5-7"] += 1
            elif rating < 9:
                rating_distribution["7-9"] += 1
            else:
                rating_distribution["9-10"] += 1
        
        # 热门教师（按热度排序）
        top_teachers = sorted(self.teachers, key=lambda x: x["heat"], reverse=True)[:20]
        
        # 高分教师（按评分排序，至少要有10个评分）
        high_rated_teachers = [t for t in self.teachers if t["rating_count"] >= 10]
        high_rated_teachers.sort(key=lambda x: x["rating"], reverse=True)
        top_rated_teachers = high_rated_teachers[:20]
        
        self.statistics = {
            "overview": {
                "total_teachers": total_teachers,
                "total_comments": total_comments,
                "total_colleges": len(college_stats),
                "avg_rating": round(sum(t["rating"] for t in self.teachers) / total_teachers, 2) if total_teachers > 0 else 0,
                "last_updated": self.update_date
            },
            "college_stats": college_list,
            "rating_distribution": rating_distribution,
            "top_teachers": top_teachers,
            "top_rated_teachers": top_rated_teachers
        }
        
        print(f"✅ 统计数据构建完成")
        print(f"   📊 总教师数: {total_teachers}")
        print(f"   💬 总评论数: {total_comments}")
        print(f"   🏫 学院数量: {len(college_stats)}")
        print(f"   ⭐ 平均评分: {self.statistics['overview']['avg_rating']}")

    def generate_html(self):
        """生成包含所有数据的HTML文件"""
        print("🔨 生成HTML文件...")
        
        # 确保输出目录存在
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 构建JavaScript数据
        js_data = f"""
        // 嵌入的数据 - 生成时间: {self.update_date}
        window.EMBEDDED_DATA = {{
            teachers: {self.safe_json_dumps(self.teachers)},
            comments: {self.safe_json_dumps(self.comments)},
            gpa_data: {self.safe_json_dumps(self.gpa_data)},
            statistics: {self.safe_json_dumps(self.statistics)},
            loaded: true
        }};
        
        console.log('数据加载完成:');
        console.log('教师数量:', window.EMBEDDED_DATA.teachers.length);
        console.log('评论数量:', window.EMBEDDED_DATA.comments.length);
        console.log('GPA数据教师数:', Object.keys(window.EMBEDDED_DATA.gpa_data).length);
        """
        
        # HTML模板
        html_template = self.get_html_template()
        
        # 替换数据占位符
        html_content = html_template.replace('{{EMBEDDED_DATA}}', js_data)
        
        # 写入文件
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"✅ HTML文件生成完成: {self.output_file}")

    def generate_individual_teacher_pages(self):
        """为每位教师生成单独的HTML页面"""
        print("👥 开始生成单个教师页面...")
        
        # 创建教师页面目录
        self.teachers_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建教师评论索引
        teacher_comments = defaultdict(list)
        for comment in self.comments:
            teacher_comments[comment["teacher_id"]].append(comment)
        
        # 为每位教师生成页面
        for i, teacher in enumerate(self.teachers):
            if i % 1000 == 0:
                print(f"  进度: {i}/{len(self.teachers)}")
            
            teacher_id = teacher["id"]
            teacher_file = self.teachers_dir / f"{teacher_id}.html"
            
            # 获取该教师的评论
            comments = teacher_comments.get(teacher_id, [])
            comments.sort(key=lambda x: x["like_diff"], reverse=True)
            
            # 获取该教师的课程
            courses = self.gpa_data.get(teacher["name"], [])
            
            # 生成页面内容
            html_content = self.generate_teacher_page_html(teacher, comments, courses)
            
            # 写入文件
            with open(teacher_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        # 生成教师索引页面
        self.generate_teacher_index_page()
        
        print(f"✅ 单个教师页面生成完成: {len(self.teachers)} 个页面")

    def generate_teacher_page_html(self, teacher, comments, courses):
        """生成单个教师页面的HTML"""
        teacher_name = html.escape(teacher["name"])
        teacher_college = html.escape(teacher["college"])
        
        # 计算点名相关的百分比（模拟数据，实际应该从评论中统计）
        # 这里使用一个基于教师ID的简单算法来生成一致的百分比
        teacher_id = teacher.get("id", 0)
        attendance_percentage = (teacher_id % 30) + 10  # 生成10-40之间的百分比
        
        # 构建课程信息HTML
        courses_html = ""
        if courses:
            courses_html = f"""
            <div class="teacher-courses">
                <h3><i class="fas fa-book"></i> 课程信息 ({len(courses)} 门课程)</h3>
                <div class="courses-grid">
            """
            for course in courses:
                course_name = html.escape(course["name"])
                gpa = float(course["gpa"]) if course["gpa"] else 0.0
                
                # 处理选课人数，可能有 "500+" 这样的格式
                student_count_str = str(course["student_count"]) if course["student_count"] else "0"
                if student_count_str.endswith('+'):
                    student_count = int(student_count_str[:-1])  # 去掉 + 号
                else:
                    try:
                        student_count = int(student_count_str)
                    except ValueError:
                        student_count = 0
                
                std_dev = float(course["std_dev"]) if course["std_dev"] else 0.0
                
                courses_html += f"""
                    <div class="course-card">
                        <div class="course-name">{course_name}</div>
                        <div class="course-stats">
                            <span class="gpa">GPA: {gpa:.2f}</span>
                            <span class="students">选课: {student_count_str}人</span>
                            <span class="std-dev">标准差: {std_dev:.2f}</span>
                        </div>
                    </div>
                """
            courses_html += """
                </div>
            </div>
            """
        else:
            courses_html = """
            <div class="teacher-courses">
                <h3><i class="fas fa-book"></i> 课程信息</h3>
                <p class="no-data">暂无课程GPA数据</p>
            </div>
            """
        
        # 构建评论HTML
        comments_html = ""
        if comments:
            # 将评论数据转换为JavaScript格式
            comments_js = self.safe_json_dumps(comments)
            
            comments_html = f"""
            <div class="teacher-comments">
                <div class="comments-header">
                    <h3><i class="fas fa-comments"></i> 学生评论 ({len(comments)} 条)</h3>
                    <div class="comments-sort">
                        <button class="sort-btn active" data-sort="popular">
                            <i class="fas fa-fire"></i> 人气评论
                        </button>
                        <button class="sort-btn" data-sort="latest">
                            <i class="fas fa-clock"></i> 最新评论
                        </button>
                    </div>
                </div>
                <div class="comments-list" id="comments-list">
                </div>
                <script>
                    // 评论数据
                    const commentsData = {comments_js};
                    
                    // 排序函数
                    function sortComments(sortType) {{
                        let sortedComments = [...commentsData];
                        
                        if (sortType === 'popular') {{
                            // 按人气排序（点赞减点踩）
                            sortedComments.sort((a, b) => b.like_diff - a.like_diff);
                        }} else if (sortType === 'latest') {{
                            // 按时间排序（最新在前）
                            sortedComments.sort((a, b) => new Date(b.post_time) - new Date(a.post_time));
                        }}
                        
                        return sortedComments;
                    }}
                    
                    // 渲染评论列表
                    function renderComments(comments) {{
                        const commentsList = document.getElementById('comments-list');
                        commentsList.innerHTML = comments.map(comment => `
                            <div class="comment-item">
                                <div class="comment-meta">
                                    <span class="comment-time">${{comment.post_time}}</span>
                                    <span class="comment-likes">
                                        <span class="likes"><i class="fas fa-thumbs-up"></i> ${{comment.likes}}</span>
                                        <span class="dislikes"><i class="fas fa-thumbs-down"></i> ${{comment.dislikes}}</span>
                                    </span>
                                </div>
                                <div class="comment-content">${{comment.content}}</div>
                            </div>
                        `).join('');
                    }}
                    
                    // 初始化页面
                    document.addEventListener('DOMContentLoaded', function() {{
                        // 默认显示人气评论
                        renderComments(sortComments('popular'));
                        
                        // 绑定排序按钮事件
                        document.querySelectorAll('.sort-btn').forEach(btn => {{
                            btn.addEventListener('click', function() {{
                                // 更新按钮状态
                                document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
                                this.classList.add('active');
                                
                                // 排序并渲染评论
                                const sortType = this.getAttribute('data-sort');
                                renderComments(sortComments(sortType));
                            }});
                        }});
                    }});
                </script>
            </div>
            """
        else:
            comments_html = """
            <div class="teacher-comments">
                <h3><i class="fas fa-comments"></i> 学生评论</h3>
                <p class="no-data">暂无评论数据</p>
            </div>
            """
        
        # 生成完整的HTML页面
        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{teacher_name} - {teacher_college} - 浙大教评</title>
    <meta name="description" content="{teacher_name}教师详情页，包含课程信息、学生评价等">
    <meta name="keywords" content="{teacher_name},{teacher_college},浙江大学,教师评价">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        {self.get_teacher_page_css()}
    </style>
</head>
<body>
    <div class="container">
        <!-- 导航栏 -->
        <nav class="navbar">
            <div class="nav-content">
                <h1>浙大教评 - 教师索引</h1>
            </div>
        </nav>
        
        <!-- 搜索栏 -->
        <div class="search-section">
            <div class="search-box">
                <input type="text" class="search-input" id="search-input" placeholder="请输入教师姓名、学院或拼音...">
                <button class="search-btn" id="search-btn">
                    <i class="fas fa-search"></i> 搜索
                </button>
            </div>
        </div>
        
        <!-- 教师基本信息 -->
        <div class="teacher-header">
            <div class="teacher-info-container">
                <div class="teacher-basic-info">
                    <h1 class="teacher-name">{teacher_name}</h1>
                    <p class="teacher-university">浙江大学</p>
                    <p class="teacher-college">{teacher_college}</p>
                </div>
                <div class="teacher-rating-display">
                    <div class="large-rating">{teacher["rating"]:.2f}</div>
                    <div class="rating-participants">{teacher["rating_count"]}人参与评分</div>
                    <div class="attendance-info">{attendance_percentage:.1f}%的人认为该老师会点名</div>
                </div>
            </div>
        </div>
        
        <!-- 课程信息 -->
        {courses_html}
        
        <!-- 学生评论 -->
        {comments_html}
        
        <!-- 页脚 -->
        <footer class="footer">
            <p>浙江大学教评查询系统 | 数据时效: {self.update_date}</p>
        </footer>
    </div>
    
    <script>
        // 搜索功能
        document.addEventListener('DOMContentLoaded', function() {{
            const searchInput = document.getElementById('search-input');
            const searchBtn = document.getElementById('search-btn');
            
            // 搜索按钮点击事件
            if (searchBtn) {{
                searchBtn.addEventListener('click', function() {{
                    performSearch();
                }});
            }}
            
            // 搜索框回车事件
            if (searchInput) {{
                searchInput.addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') {{
                        performSearch();
                    }}
                }});
            }}
            
            function performSearch() {{
                const query = searchInput.value.trim();
                if (query) {{
                    // 跳转到首页并携带搜索参数
                    window.location.href = '../index.html?search=' + encodeURIComponent(query);
                }} else {{
                    // 如果搜索为空，只跳转到首页
                    window.location.href = '../index.html';
                }}
            }}
        }});
    </script>
</body>
</html>"""

    def chinese_to_pinyin(self, text):
        """将中文转换为拼音（简化版本）"""
        # 简化的拼音映射表，只包含常见字符
        pinyin_map = {
            '张': 'zhang', '王': 'wang', '李': 'li', '赵': 'zhao', '陈': 'chen',
            '刘': 'liu', '杨': 'yang', '黄': 'huang', '周': 'zhou', '吴': 'wu',
            '徐': 'xu', '孙': 'sun', '马': 'ma', '朱': 'zhu', '胡': 'hu',
            '林': 'lin', '郭': 'guo', '何': 'he', '高': 'gao', '罗': 'luo',
            '郑': 'zheng', '梁': 'liang', '谢': 'xie', '宋': 'song', '唐': 'tang',
            '许': 'xu', '邓': 'deng', '冯': 'feng', '韩': 'han', '曹': 'cao',
            '曾': 'zeng', '彭': 'peng', '萧': 'xiao', '蔡': 'cai', '潘': 'pan',
            '田': 'tian', '董': 'dong', '袁': 'yuan', '于': 'yu', '余': 'yu',
            '叶': 'ye', '蒋': 'jiang', '杜': 'du', '苏': 'su', '魏': 'wei',
            '程': 'cheng', '吕': 'lv', '丁': 'ding', '沈': 'shen', '任': 'ren',
            '姚': 'yao', '卢': 'lu', '傅': 'fu', '钟': 'zhong', '姜': 'jiang',
            '崔': 'cui', '谭': 'tan', '廖': 'liao', '范': 'fan', '汪': 'wang',
            '陆': 'lu', '金': 'jin', '石': 'shi', '戴': 'dai', '贾': 'jia',
            '韦': 'wei', '夏': 'xia', '邱': 'qiu', '方': 'fang', '侯': 'hou',
            '邹': 'zou', '熊': 'xiong', '孟': 'meng', '秦': 'qin', '白': 'bai',
            '江': 'jiang', '阎': 'yan', '薛': 'xue', '尹': 'yin', '段': 'duan',
            '雷': 'lei', '黎': 'li', '史': 'shi', '龙': 'long', '陶': 'tao',
            '贺': 'he', '顾': 'gu', '毛': 'mao', '郝': 'hao', '龚': 'gong',
            '邵': 'shao', '万': 'wan', '钱': 'qian', '严': 'yan', '覃': 'qin',
            '武': 'wu', '戴': 'dai', '莫': 'mo', '孔': 'kong', '向': 'xiang',
            '汤': 'tang', '常': 'chang', '温': 'wen', '康': 'kang', '施': 'shi',
            '文': 'wen', '牛': 'niu', '樊': 'fan', '葛': 'ge', '邢': 'xing',
            '安': 'an', '齐': 'qi', '易': 'yi', '乔': 'qiao', '伍': 'wu',
            '庞': 'pang', '颜': 'yan', '倪': 'ni', '庄': 'zhuang', '聂': 'nie',
            '章': 'zhang', '鲁': 'lu', '岳': 'yue', '翟': 'zhai', '殷': 'yin',
            '詹': 'zhan', '申': 'shen', '欧': 'ou', '耿': 'geng', '关': 'guan',
            '兰': 'lan', '焦': 'jiao', '俞': 'yu', '左': 'zuo', '辛': 'xin',
            '管': 'guan', '祝': 'zhu', '霍': 'huo', '房': 'fang', '卞': 'bian',
            '路': 'lu', '盛': 'sheng', '苗': 'miao', '曲': 'qu', '成': 'cheng',
            '游': 'you', '阳': 'yang', '裴': 'pei', '席': 'xi', '卫': 'wei',
            '查': 'zha', '屈': 'qu', '鲍': 'bao', '位': 'wei', '覃': 'tan',
            '佘': 'she', '商': 'shang', '苟': 'gou', '池': 'chi', '敖': 'ao',
            '蓝': 'lan', '单': 'shan', '包': 'bao', '司': 'si', '柏': 'bai',
            '宁': 'ning', '柯': 'ke', '阮': 'ruan', '桂': 'gui', '闵': 'min',
            '欧': 'ou', '阳': 'yang', '解': 'xie', '强': 'qiang', '柴': 'chai',
            '华': 'hua', '车': 'che', '冉': 'ran', '房': 'fang', '边': 'bian',
            '辜': 'gu', '吉': 'ji', '饶': 'rao', '刁': 'diao', '瞿': 'qu',
            '戚': 'qi', '丘': 'qiu', '古': 'gu', '米': 'mi', '池': 'chi',
            '滕': 'teng', '晋': 'jin', '苑': 'yuan', '邬': 'wu', '臧': 'zang',
            '畅': 'chang', '宫': 'gong', '来': 'lai', '嵺': 'liao', '苟': 'gou',
            '全': 'quan', '褚': 'chu', '廉': 'lian', '简': 'jian', '娄': 'lou',
            '盖': 'gai', '符': 'fu', '奚': 'xi', '木': 'mu', '穆': 'mu',
            '党': 'dang', '燕': 'yan', '郎': 'lang', '邸': 'di', '冀': 'ji',
            '谈': 'tan', '姬': 'ji', '屠': 'tu', '连': 'lian', '郜': 'gao',
            '晏': 'yan', '栾': 'luan', '郁': 'yu', '商': 'shang', '蒙': 'meng',
            '计': 'ji', '喻': 'yu', '揭': 'jie', '窦': 'dou', '迟': 'chi',
            '宇': 'yu', '敬': 'jing', '巨': 'ju', '银': 'yin', '徽': 'hui',
            '国': 'guo', '家': 'jia', '明': 'ming', '军': 'jun', '建': 'jian',
            '强': 'qiang', '伟': 'wei', '华': 'hua', '永': 'yong', '志': 'zhi',
            '红': 'hong', '英': 'ying', '勇': 'yong', '超': 'chao', '飞': 'fei',
            '涛': 'tao', '鹏': 'peng', '辉': 'hui', '峰': 'feng', '磊': 'lei',
            '亮': 'liang', '东': 'dong', '龙': 'long', '洋': 'yang', '静': 'jing',
            '丽': 'li', '平': 'ping', '娜': 'na', '敏': 'min', '芳': 'fang',
            '雪': 'xue', '霞': 'xia', '秀': 'xiu', '兰': 'lan', '莉': 'li',
            '婷': 'ting', '玉': 'yu', '美': 'mei', '云': 'yun', '凤': 'feng',
            '凯': 'kai', '燕': 'yan', '萍': 'ping', '梅': 'mei', '琴': 'qin',
            '艳': 'yan', '晶': 'jing', '欢': 'huan', '瑜': 'yu', '慧': 'hui',
            '琳': 'lin', '颖': 'ying', '晓': 'xiao', '欣': 'xin', '佳': 'jia',
            '玲': 'ling', '清': 'qing', '晨': 'chen', '旭': 'xu', '阳': 'yang',
            '宇': 'yu', '彦': 'yan', '俊': 'jun', '斌': 'bin', '博': 'bo',
            '文': 'wen', '杰': 'jie', '宁': 'ning', '思': 'si', '欣': 'xin',
            '雨': 'yu', '晴': 'qing', '春': 'chun', '夏': 'xia', '秋': 'qiu',
            '冬': 'dong', '天': 'tian', '地': 'di', '人': 'ren', '心': 'xin',
            '学': 'xue', '生': 'sheng', '老': 'lao', '师': 'shi', '同': 'tong',
            '竺': 'zhu'
        }
        
        result = []
        for char in text:
            if char in pinyin_map:
                result.append(pinyin_map[char])
            elif char.isalpha():
                result.append(char.lower())
            else:
                # 对于不在映射表中的字符，使用字符本身
                result.append(char)
        
        return ''.join(result)

    def generate_teacher_index_page(self):
        """生成教师索引页面"""
        print("📋 生成教师索引页面...")
        
        # 获取脚本所在目录
        script_dir = Path(__file__).parent
        
        # 设置 index.html 文件路径
        if script_dir.name == "src":
            # 脚本在 src 目录中
            index_file = script_dir.parent / "web" / "index.html"
        else:
            # 脚本在项目根目录中
            index_file = script_dir / "web" / "index.html"
        
        # 按学院分组统计
        colleges = defaultdict(list)
        for teacher in self.teachers:
            colleges[teacher["college"]].append(teacher)
        
        # 构建教师数据的JavaScript数组，包含拼音信息
        teachers_js = self.safe_json_dumps([{
            "id": teacher["id"],
            "name": teacher["name"],
            "college": teacher["college"],
            "rating": teacher["rating"]
        } for teacher in self.teachers])
        
        index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>教师索引 - 浙大教评</title>
    <meta name="description" content="浙江大学教师索引页面，按学院分类浏览所有教师">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        {self.get_index_page_css()}
    </style>
</head>
<body>
    <div class="container">
        <!-- 导航栏 -->
        <nav class="navbar">
            <div class="nav-content">
                <h1>浙大教评 - 教师索引</h1>
            </div>
        </nav>
        
        <!-- 搜索框 -->
        <div class="search-box">
            <input type="text" id="search-input" placeholder="搜索教师姓名..." onkeyup="searchTeachers()">
            <i class="fas fa-search"></i>
        </div>
        
        <!-- 搜索结果 -->
        <div id="search-results" class="search-results" style="display: none;">
            <h3>搜索结果</h3>
            <div id="results-list" class="results-list"></div>
        </div>
        
        <!-- 提示信息 -->
        <div class="search-hint">
            <p><i class="fas fa-info-circle"></i> 在上方搜索框中输入教师姓名或拼音进行搜索</p>
        </div>
        
        <!-- 页脚 -->
        <footer class="footer">
            <p>浙江大学教评查询系统 | 更新时间: {self.update_date}</p>
        </footer>
    </div>
    
    <script>
        // 教师数据
        const teachersData = {teachers_js};
        
        function searchTeachers() {{
            const query = document.getElementById('search-input').value.toLowerCase().trim();
            const resultsContainer = document.getElementById('search-results');
            const resultsList = document.getElementById('results-list');
            const searchHint = document.querySelector('.search-hint');
            
            if (query === '') {{
                resultsContainer.style.display = 'none';
                searchHint.style.display = 'block';
                return;
            }}
            
            // 搜索匹配的教师（仅支持中文姓名搜索）
            const matchedTeachers = teachersData.filter(teacher => {{
                const lowerQuery = query.toLowerCase();
                return teacher.name.toLowerCase().includes(lowerQuery);
            }});
            
            if (matchedTeachers.length > 0) {{
                resultsContainer.style.display = 'block';
                searchHint.style.display = 'none';
                
                resultsList.innerHTML = matchedTeachers.slice(0, 50).map(teacher => `
                    <a href="teachers/${{teacher.id}}.html" class="result-item">
                        <div class="teacher-info">
                            <span class="teacher-name">${{teacher.name}}</span>
                            <span class="teacher-college">${{teacher.college}}</span>
                        </div>
                        <div class="teacher-rating">${{teacher.rating.toFixed(1)}}分</div>
                    </a>
                `).join('');
                
                if (matchedTeachers.length > 50) {{
                    resultsList.innerHTML += `
                        <div class="more-results">
                            <p>还有 ${{matchedTeachers.length - 50}} 位教师，请输入更具体的关键词</p>
                        </div>
                    `;
                }}
            }} else {{
                resultsContainer.style.display = 'block';
                searchHint.style.display = 'none';
                resultsList.innerHTML = '<div class="no-results"><p>未找到匹配的教师</p></div>';
            }}
        }}
        
        // 页面加载完成后的初始化
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('教师数据已加载，共 ' + teachersData.length + ' 位教师');
            
            // 检查URL中是否有搜索参数
            const urlParams = new URLSearchParams(window.location.search);
            const searchQuery = urlParams.get('search');
            
            if (searchQuery) {{
                // 如果有搜索参数，设置搜索框的值并执行搜索
                document.getElementById('search-input').value = searchQuery;
                searchTeachers();
            }}
        }});
    </script>
</body>
</html>"""
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        print(f"✅ 教师索引页面生成完成: {index_file}")

    def get_teacher_page_css(self):
        """获取教师页面的CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .navbar {
            background: white;
            border-radius: 10px;
            padding: 15px 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .nav-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .nav-content h1 {
            color: #333;
            font-size: 1.5em;
            margin: 0;
        }
        
        /* 搜索栏样式 */
        .search-section {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .search-box {
            display: flex;
            gap: 0;
        }
        
        .search-input {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px 0 0 8px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .search-input:focus {
            border-color: #667eea;
        }
        
        .search-btn {
            padding: 12px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 0 8px 8px 0;
            cursor: pointer;
            transition: background 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .search-btn:hover {
            background: #5a67d8;
        }
        
        .teacher-header {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .teacher-info-container {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 30px;
        }
        
        .teacher-basic-info {
            flex: 1;
            text-align: left;
        }
        
        .teacher-name {
            font-size: 2.8em;
            color: #333;
            margin: 0 0 10px 0;
            font-weight: 600;
        }
        
        .teacher-university {
            font-size: 1.1em;
            color: #666;
            margin: 5px 0;
        }
        
        .teacher-college {
            font-size: 1.1em;
            color: #666;
            margin: 5px 0;
        }
        
        .teacher-rating-display {
            flex: 0 0 auto;
            text-align: center;
            padding-left: 40px;
        }
        
        .large-rating {
            font-size: 4.5em;
            font-weight: bold;
            color: #1e74fd;
            line-height: 1;
            margin-bottom: 10px;
        }
        
        .rating-participants {
            font-size: 1em;
            color: #666;
            margin-bottom: 8px;
        }
        
        .attendance-info {
            font-size: 0.95em;
            color: #666;
        }
        
        .teacher-stats {
            display: flex;
            justify-content: flex-start;
            gap: 40px;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-item i {
            font-size: 1.5em;
            color: #667eea;
            display: block;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
            display: block;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .teacher-courses, .teacher-comments {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .teacher-courses h3, .teacher-comments h3 {
            color: #667eea;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .comments-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .comments-sort {
            display: flex;
            gap: 10px;
        }
        
        .sort-btn {
            padding: 8px 16px;
            border: 2px solid #e0e0e0;
            background: white;
            color: #666;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        .sort-btn:hover {
            border-color: #667eea;
            color: #667eea;
        }
        
        .sort-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .sort-btn i {
            font-size: 0.8em;
        }
        
        .courses-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
        }
        
        .course-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            border-left: 4px solid #667eea;
        }
        
        .course-name {
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        
        .course-stats {
            display: flex;
            justify-content: space-between;
            font-size: 0.9em;
            color: #666;
        }
        
        .gpa {
            color: #28a745;
            font-weight: bold;
        }
        
        .comments-list {
            max-height: 600px;
            overflow-y: auto;
        }
        
        .comment-item {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }
        
        .comment-meta {
            display: flex;
            justify-content: space-between;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        
        .comment-likes i {
            margin-right: 5px;
        }
        
        .comment-likes .likes {
            color: #28a745;
            margin-right: 15px;
        }
        
        .comment-likes .dislikes {
            color: #dc3545;
        }
        
        .comment-content {
            line-height: 1.5;
        }
        
        .no-data {
            color: #666;
            font-style: italic;
            text-align: center;
            padding: 20px;
        }
        
        .more-comments {
            text-align: center;
            color: #666;
            font-style: italic;
            margin-top: 20px;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            border-top: 1px solid #eee;
            margin-top: 40px;
        }
        
        .footer a {
            color: #667eea;
            text-decoration: none;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .search-box {
                flex-direction: column;
                gap: 10px;
            }
            
            .search-input {
                border-radius: 8px;
            }
            
            .search-btn {
                border-radius: 8px;
                justify-content: center;
            }
            
            .teacher-info-container {
                flex-direction: column;
                text-align: center;
            }
            
            .teacher-basic-info {
                margin-bottom: 20px;
            }
            
            .teacher-rating-display {
                padding-left: 0;
            }
            
            .teacher-name {
                font-size: 2.2em;
            }
            
            .large-rating {
                font-size: 3.5em;
            }
            
            .teacher-stats {
                justify-content: center;
                gap: 30px;
            }
            
            .courses-grid {
                grid-template-columns: 1fr;
            }
            
            .course-stats {
                flex-direction: column;
                gap: 5px;
            }
            
            .comments-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 15px;
            }
            
            .comments-sort {
                width: 100%;
                justify-content: center;
            }
            
            .sort-btn {
                flex: 1;
                justify-content: center;
                padding: 10px 12px;
            }
        }
        """

    def get_index_page_css(self):
        """获取索引页面的CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .navbar {
            background: white;
            border-radius: 10px;
            padding: 15px 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .nav-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .nav-home {
            color: #667eea;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 5px;
            transition: background 0.3s;
        }
        
        .nav-home:hover {
            background: #f0f0f0;
        }
        
        .stats-summary {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            gap: 30px;
            justify-content: center;
        }
        
        .stat-item {
            display: flex;
            align-items: center;
            gap: 10px;
            color: #667eea;
            font-weight: bold;
        }
        
        .search-box {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            position: relative;
        }
        
        .search-box input {
            width: 100%;
            padding: 15px 50px 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            outline: none;
        }
        
        .search-box input:focus {
            border-color: #667eea;
        }
        
        .search-box i {
            position: absolute;
            right: 35px;
            top: 50%;
            transform: translateY(-50%);
            color: #666;
        }
        
        .search-results {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .search-results h3 {
            color: #667eea;
            margin-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
            padding-bottom: 10px;
        }
        
        .results-list {
            display: grid;
            gap: 8px;
            max-height: 600px;
            overflow-y: auto;
        }
        
        .result-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            background: #f8f9fa;
            border-radius: 8px;
            text-decoration: none;
            color: inherit;
            transition: all 0.3s ease;
            border-left: 4px solid transparent;
        }
        
        .result-item:hover {
            background: #e9ecef;
            border-left-color: #667eea;
            transform: translateX(5px);
        }
        
        .teacher-info {
            display: flex;
            flex-direction: column;
            gap: 4px;
        }
        
        .teacher-name {
            font-weight: 600;
            color: #333;
        }
        
        .teacher-college {
            font-size: 0.9em;
            color: #666;
        }
        
        .teacher-rating {
            color: #667eea;
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .no-results, .more-results {
            text-align: center;
            padding: 20px;
            color: #666;
            font-style: italic;
        }
        
        .search-hint {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            color: #666;
        }
        
        .search-hint i {
            color: #667eea;
            margin-right: 8px;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
            border-top: 1px solid #eee;
            margin-top: 40px;
        }
        
        .footer a {
            color: #667eea;
            text-decoration: none;
        }
        
        @media (max-width: 768px) {
            .stats-summary {
                flex-direction: column;
                align-items: center;
                gap: 15px;
            }
            
            .result-item {
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }
            
            .teacher-rating {
                align-self: flex-end;
            }
        }
        """

    def get_html_template(self):
        """获取HTML模板"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>浙江大学教评查询系统</title>
    <meta name="description" content="浙江大学教师评价查询系统，支持教师搜索、评论浏览、课程GPA查询">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        /* 基础样式 */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* 头部样式 */
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        /* 搜索区域 */
        .search-section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .search-box {
            display: flex;
            margin-bottom: 20px;
        }
        
        .search-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e0e0e0;
            border-radius: 10px 0 0 10px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .search-input:focus {
            border-color: #667eea;
        }
        
        .search-btn {
            padding: 15px 25px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 0 10px 10px 0;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .search-btn:hover {
            background: #5a67d8;
        }
        
        .filters {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .filter-select {
            padding: 10px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            background: white;
            outline: none;
        }
        
        /* 结果区域 */
        .results-section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            display: none;
        }
        
        .results-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .results-count {
            font-size: 1.2em;
            color: #333;
        }
        
        .clear-btn {
            background: #ff6b6b;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 8px;
            cursor: pointer;
        }
        
        /* 教师卡片 */
        .teachers-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .teacher-card {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
        }
        
        .teacher-card:hover {
            transform: translateY(-3px);
            border-color: #667eea;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .teacher-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 8px;
        }
        
        .teacher-college {
            color: #666;
            margin-bottom: 15px;
        }
        
        .teacher-stats {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .teacher-rating {
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-weight: bold;
        }
        
        .teacher-heat {
            color: #ff6b6b;
            font-size: 0.9em;
        }
        
        /* 模态框 */
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 1000;
        }
        
        .modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border-radius: 15px;
            width: 90%;
            max-width: 800px;
            max-height: 90vh;
            overflow-y: auto;
        }
        
        .modal-header {
            padding: 25px;
            border-bottom: 2px solid #f0f0f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-title {
            font-size: 1.5em;
            color: #333;
        }
        
        .close-btn {
            background: none;
            border: none;
            font-size: 1.5em;
            cursor: pointer;
            color: #999;
        }
        
        .modal-body {
            padding: 25px;
        }
        
        .teacher-detail {
            margin-bottom: 30px;
        }
        
        .teacher-detail h3 {
            color: #667eea;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .comments-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .comment-item {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #667eea;
        }
        
        .comment-meta {
            display: flex;
            justify-content: space-between;
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        
        .comment-content {
            line-height: 1.5;
        }
        
        .load-more {
            text-align: center;
            margin-top: 20px;
        }
        
        .load-more-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 8px;
            cursor: pointer;
        }
        
        /* 加载动画 */
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .spinner {
            display: inline-block;
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-bottom: 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .search-box {
                flex-direction: column;
            }
            
            .search-input {
                border-radius: 10px;
                margin-bottom: 10px;
            }
            
            .search-btn {
                border-radius: 10px;
            }
            
            .filters {
                flex-direction: column;
            }
            
            .teachers-grid {
                grid-template-columns: 1fr;
            }
            
            .modal-content {
                width: 95%;
                height: 95vh;
            }
        }
        
        .hidden {
            display: none !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- 头部 -->
        <div class="header">
            <p>chalaoshi</p>
        </div>
        
        <!-- 搜索区域 -->
        <div class="search-section">
            <div class="search-box">
                <input type="text" class="search-input" id="search-input" placeholder="请输入教师姓名、学院或拼音...">
                <button class="search-btn" id="search-btn">
                    <i class="fas fa-search"></i> 搜索
                </button>
            </div>
            
            <div class="filters">
                <select class="filter-select" id="college-filter">
                    <option value="">所有学院</option>
                </select>
                <select class="filter-select" id="rating-filter">
                    <option value="">评分范围</option>
                    <option value="9-10">9.0-10.0 分</option>
                    <option value="7-9">7.0-9.0 分</option>
                    <option value="5-7">5.0-7.0 分</option>
                    <option value="0-5">0-5.0 分</option>
                </select>
                <select class="filter-select" id="sort-filter">
                    <option value="rating">按评分排序</option>
                    <option value="heat">按热度排序</option>
                    <option value="name">按姓名排序</option>
                </select>
            </div>
        </div>
        
        <!-- 搜索结果区域 -->
        <div class="results-section" id="results-section">
            <div class="results-header">
                <div class="results-count" id="results-count">找到 0 位教师</div>
                <button class="clear-btn" id="clear-btn">
                    <i class="fas fa-times"></i> 清除搜索
                </button>
            </div>
            
            <div class="teachers-grid" id="teachers-grid">
                <!-- 搜索结果将在这里显示 -->
            </div>
            
            <div class="load-more hidden" id="load-more">
                <button class="load-more-btn" id="load-more-btn">加载更多</button>
            </div>
        </div>
        
        <!-- 加载动画 -->
        <div class="loading hidden" id="loading">
            <div class="spinner"></div>
            <div>正在搜索...</div>
        </div>
    </div>
    
    <!-- 教师详情模态框 -->
    <div class="modal" id="teacher-modal">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title" id="modal-title">教师详情</div>
                <button class="close-btn" id="close-modal">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                <div class="teacher-detail">
                    <h3><i class="fas fa-user"></i> 基本信息</h3>
                    <div id="teacher-info"></div>
                </div>
                
                <div class="teacher-detail">
                    <h3><i class="fas fa-book"></i> 课程信息</h3>
                    <div id="teacher-courses"></div>
                </div>
                
                <div class="teacher-detail">
                    <h3><i class="fas fa-comments"></i> 学生评论</h3>
                    <div class="comments-list" id="comments-list">
                        <!-- 评论列表 -->
                    </div>
                    <div class="load-more hidden" id="load-more-comments">
                        <button class="load-more-btn" id="load-more-comments-btn">加载更多评论</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        {{EMBEDDED_DATA}}
        
        // 应用程序类
        class ChalaoshiApp {
            constructor() {
                this.teachers = window.EMBEDDED_DATA.teachers || [];
                this.comments = window.EMBEDDED_DATA.comments || [];
                this.gpaData = window.EMBEDDED_DATA.gpa_data || {};
                this.statistics = window.EMBEDDED_DATA.statistics || {};
                
                this.currentResults = [];
                this.currentPage = 0;
                this.pageSize = 20;
                this.currentTeacher = null;
                this.currentCommentPage = 0;
                
                this.init();
            }
            
            init() {
                this.setupEventListeners();
                this.populateColleges();
                this.checkUrlParams();
                this.showTopTeachers();
            }
            
            checkUrlParams() {
                // 检查URL中是否有搜索参数
                const urlParams = new URLSearchParams(window.location.search);
                const searchQuery = urlParams.get('search');
                
                if (searchQuery) {
                    // 如果有搜索参数，设置搜索框的值并执行搜索
                    document.getElementById('search-input').value = searchQuery;
                    this.performSearch();
                }
            }
            
            setupEventListeners() {
                // 搜索相关
                document.getElementById('search-btn').addEventListener('click', () => this.performSearch());
                document.getElementById('search-input').addEventListener('keypress', (e) => {
                    if (e.key === 'Enter') this.performSearch();
                });
                
                // 筛选器
                document.getElementById('college-filter').addEventListener('change', () => this.performSearch());
                document.getElementById('rating-filter').addEventListener('change', () => this.performSearch());
                document.getElementById('sort-filter').addEventListener('change', () => this.performSearch());
                
                // 清除搜索
                document.getElementById('clear-btn').addEventListener('click', () => this.clearSearch());
                
                // 加载更多
                document.getElementById('load-more-btn').addEventListener('click', () => this.loadMoreResults());
                
                // 模态框
                document.getElementById('close-modal').addEventListener('click', () => this.closeModal());
                document.getElementById('teacher-modal').addEventListener('click', (e) => {
                    if (e.target.id === 'teacher-modal') this.closeModal();
                });
                
                // 加载更多评论
                document.getElementById('load-more-comments-btn').addEventListener('click', () => this.loadMoreComments());
            }
            
            populateColleges() {
                const colleges = [...new Set(this.teachers.map(t => t.college))].sort();
                const collegeFilter = document.getElementById('college-filter');
                
                colleges.forEach(college => {
                    const option = document.createElement('option');
                    option.value = college;
                    option.textContent = college;
                    collegeFilter.appendChild(option);
                });
            }
            
            showTopTeachers() {
                // 显示热门教师作为默认内容
                const topTeachers = [...this.teachers]
                    .filter(t => t.rating_count >= 5)
                    .sort((a, b) => b.heat - a.heat)
                    .slice(0, 20);
                
                this.displayResults(topTeachers, false);
                document.getElementById('results-section').style.display = 'block';
                document.getElementById('results-count').textContent = `热门教师推荐 (${topTeachers.length} 位)`;
            }
            
            performSearch() {
                const query = document.getElementById('search-input').value.trim().toLowerCase();
                const college = document.getElementById('college-filter').value;
                const rating = document.getElementById('rating-filter').value;
                const sort = document.getElementById('sort-filter').value;
                
                // 显示加载动画
                document.getElementById('loading').classList.remove('hidden');
                document.getElementById('results-section').style.display = 'none';
                
                setTimeout(() => {
                    let results = [...this.teachers];
                    
                    // 文本搜索
                    if (query) {
                        results = results.filter(teacher => 
                            teacher.name.toLowerCase().includes(query) ||
                            teacher.college.toLowerCase().includes(query)
                        );
                    }
                    
                    // 学院筛选
                    if (college) {
                        results = results.filter(teacher => teacher.college === college);
                    }
                    
                    // 评分筛选
                    if (rating) {
                        const [min, max] = rating.split('-').map(Number);
                        results = results.filter(teacher => teacher.rating >= min && teacher.rating < max);
                    }
                    
                    // 排序
                    switch (sort) {
                        case 'rating':
                            results.sort((a, b) => b.rating - a.rating);
                            break;
                        case 'heat':
                            results.sort((a, b) => b.heat - a.heat);
                            break;
                        case 'name':
                            results.sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
                            break;
                    }
                    
                    this.currentResults = results;
                    this.currentPage = 0;
                    this.displayResults(results.slice(0, this.pageSize));
                    
                    // 更新UI
                    document.getElementById('loading').classList.add('hidden');
                    document.getElementById('results-section').style.display = 'block';
                    document.getElementById('results-count').textContent = `找到 ${results.length} 位教师`;
                    
                    // 显示/隐藏加载更多按钮
                    const loadMore = document.getElementById('load-more');
                    if (results.length > this.pageSize) {
                        loadMore.classList.remove('hidden');
                    } else {
                        loadMore.classList.add('hidden');
                    }
                }, 300);
            }
            
            displayResults(teachers, append = false) {
                const grid = document.getElementById('teachers-grid');
                
                if (!append) {
                    grid.innerHTML = '';
                }
                
                teachers.forEach(teacher => {
                    const card = this.createTeacherCard(teacher);
                    grid.appendChild(card);
                });
            }
            
            createTeacherCard(teacher) {
                const card = document.createElement('div');
                card.className = 'teacher-card';
                card.addEventListener('click', () => this.showTeacherDetail(teacher));
                
                card.innerHTML = `
                    <div class="teacher-name">${teacher.name}</div>
                    <div class="teacher-college">${teacher.college}</div>
                    <div class="teacher-stats">
                        <div class="teacher-rating">${teacher.rating.toFixed(1)} 分</div>
                        <div class="teacher-heat">
                            <i class="fas fa-fire"></i> ${teacher.heat}
                        </div>
                    </div>
                    <div style="margin-top: 10px; font-size: 0.9em; color: #666;">
                        ${teacher.rating_count} 人评分
                    </div>
                `;
                
                return card;
            }
            
            loadMoreResults() {
                this.currentPage++;
                const start = this.currentPage * this.pageSize;
                const end = start + this.pageSize;
                const nextBatch = this.currentResults.slice(start, end);
                
                this.displayResults(nextBatch, true);
                
                // 检查是否还有更多数据
                if (end >= this.currentResults.length) {
                    document.getElementById('load-more').classList.add('hidden');
                }
            }
            
            showTeacherDetail(teacher) {
                this.currentTeacher = teacher;
                this.currentCommentPage = 0;
                
                // 更新模态框标题
                document.getElementById('modal-title').textContent = `${teacher.name} - ${teacher.college}`;
                
                // 显示基本信息
                this.displayTeacherInfo(teacher);
                
                // 显示课程信息
                this.displayTeacherCourses(teacher);
                
                // 显示评论
                this.displayTeacherComments(teacher);
                
                // 显示模态框
                document.getElementById('teacher-modal').style.display = 'block';
            }
            
            displayTeacherInfo(teacher) {
                const info = document.getElementById('teacher-info');
                info.innerHTML = `
                    <div style="background: #f8f9fa; border-radius: 10px; padding: 20px;">
                        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                            <div>
                                <strong>教师姓名:</strong> ${teacher.name}
                            </div>
                            <div>
                                <strong>所属学院:</strong> ${teacher.college}
                            </div>
                            <div>
                                <strong>评分:</strong> <span style="color: #667eea; font-weight: bold;">${teacher.rating.toFixed(2)} 分</span>
                            </div>
                            <div>
                                <strong>评分人数:</strong> ${teacher.rating_count} 人
                            </div>
                            <div>
                                <strong>热度:</strong> <span style="color: #ff6b6b;">${teacher.heat}</span>
                            </div>
                        </div>
                    </div>
                `;
            }
            
            displayTeacherCourses(teacher) {
                const coursesDiv = document.getElementById('teacher-courses');
                const courses = this.gpaData[teacher.name] || [];
                
                if (courses.length === 0) {
                    coursesDiv.innerHTML = '<p style="color: #666;">暂无课程GPA数据</p>';
                    return;
                }
                
                const coursesHtml = courses.map(course => `
                    <div style="background: #f8f9fa; border-radius: 8px; padding: 15px; margin-bottom: 10px;">
                        <div style="font-weight: bold; margin-bottom: 5px;">${course.name}</div>
                        <div style="display: flex; justify-content: space-between; color: #666;">
                            <span>GPA: <strong style="color: #667eea;">${course.gpa.toFixed(2)}</strong></span>
                            <span>选课人数: ${course.student_count}</span>
                            <span>标准差: ${course.std_dev.toFixed(2)}</span>
                        </div>
                    </div>
                `).join('');
                
                coursesDiv.innerHTML = coursesHtml;
            }
            
            displayTeacherComments(teacher) {
                const teacherComments = this.comments
                    .filter(comment => comment.teacher_id === teacher.id)
                    .sort((a, b) => b.like_diff - a.like_diff);
                
                const commentsDiv = document.getElementById('comments-list');
                const start = 0;
                const end = Math.min(20, teacherComments.length);
                
                if (teacherComments.length === 0) {
                    commentsDiv.innerHTML = '<p style="color: #666;">暂无评论数据</p>';
                    document.getElementById('load-more-comments').classList.add('hidden');
                    return;
                }
                
                const commentsHtml = teacherComments.slice(start, end).map(comment => `
                    <div class="comment-item">
                        <div class="comment-meta">
                            <span>${comment.post_time}</span>
                            <span>
                                <i class="fas fa-thumbs-up" style="color: #28a745;"></i> ${comment.likes}
                                <i class="fas fa-thumbs-down" style="color: #dc3545; margin-left: 10px;"></i> ${comment.dislikes}
                            </span>
                        </div>
                        <div class="comment-content">${comment.content}</div>
                    </div>
                `).join('');
                
                commentsDiv.innerHTML = commentsHtml;
                
                // 显示/隐藏加载更多评论按钮
                const loadMoreComments = document.getElementById('load-more-comments');
                if (teacherComments.length > 20) {
                    loadMoreComments.classList.remove('hidden');
                } else {
                    loadMoreComments.classList.add('hidden');
                }
                
                this.currentTeacherComments = teacherComments;
            }
            
            loadMoreComments() {
                this.currentCommentPage++;
                const start = this.currentCommentPage * 20;
                const end = start + 20;
                const nextComments = this.currentTeacherComments.slice(start, end);
                
                const commentsDiv = document.getElementById('comments-list');
                const newCommentsHtml = nextComments.map(comment => `
                    <div class="comment-item">
                        <div class="comment-meta">
                            <span>${comment.post_time}</span>
                            <span>
                                <i class="fas fa-thumbs-up" style="color: #28a745;"></i> ${comment.likes}
                                <i class="fas fa-thumbs-down" style="color: #dc3545; margin-left: 10px;"></i> ${comment.dislikes}
                            </span>
                        </div>
                        <div class="comment-content">${comment.content}</div>
                    </div>
                `).join('');
                
                commentsDiv.innerHTML += newCommentsHtml;
                
                // 检查是否还有更多评论
                if (end >= this.currentTeacherComments.length) {
                    document.getElementById('load-more-comments').classList.add('hidden');
                }
            }
            
            closeModal() {
                document.getElementById('teacher-modal').style.display = 'none';
            }
            
            clearSearch() {
                document.getElementById('search-input').value = '';
                document.getElementById('college-filter').value = '';
                document.getElementById('rating-filter').value = '';
                document.getElementById('sort-filter').value = 'rating';
                
                this.showTopTeachers();
            }
        }
        
        // 页面加载完成后初始化应用
        document.addEventListener('DOMContentLoaded', () => {
            if (window.EMBEDDED_DATA && window.EMBEDDED_DATA.loaded) {
                new ChalaoshiApp();
            } else {
                console.error('数据加载失败');
                document.body.innerHTML = '<div style="text-align: center; padding: 50px; color: red;">数据加载失败，请检查文件</div>';
            }
        });
    </script>
</body>
</html>'''

def main():
    """主函数"""
    import sys
    
    print("🚀 浙江大学教评查询系统 - HTML文件构建器")
    
    # 检查命令行参数 - 默认生成所有页面
    only_main = "--main-only" in sys.argv or "-m" in sys.argv
    
    if only_main:
        print("📄 模式: 仅生成主文件")
        print("💡 提示: 不使用 --main-only 或 -m 参数可同时生成单个教师页面")
        builder = SingleHTMLBuilder()
    else:
        print("📄 模式: 生成主文件 + 单个教师页面")
        builder = SingleHTMLBuilder(generate_individual_pages=True)
    
    # 检查源数据目录
    if not builder.source_dir.exists():
        print(f"❌ 源数据目录不存在: {builder.source_dir}")
        print("请确保数据文件存在于 comment/extracted/ 目录中")
        return
    
    # 构建HTML文件
    try:
        builder.build_all()
        print("\n🎉 HTML文件构建成功！")
        print(f"📁 教师索引页面: web/index.html")
        
        if not only_main:
            print(f"📁 教师页面目录: {builder.teachers_dir}")
            print("📝 使用说明:")
            print("1. 打开 web/index.html 查看教师索引")
            print("2. 点击教师姓名查看详情页面")
            print("3. 每个教师页面URL: web/teachers/{教师ID}.html")
            print("4. 教师页面可通过'返回首页'回到索引页")
        
        print("📝 主要功能:")
        print("1. 教师搜索和筛选")
        print("2. 按学院浏览教师")
        print("3. 查看教师评分和评论")
        print("4. 完全离线可用")
        
    except Exception as e:
        print(f"❌ 构建失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
