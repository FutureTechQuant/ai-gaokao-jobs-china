import json
import os
import re
from collections import Counter, defaultdict
from typing import Any, Dict, List, Set, Tuple
import pandas as pd
import numpy as np

def fix_all_json_analysis():
    """修复 all.json 分析，正确提取专业数据"""
    print("🔧 修复 all.json 数据分析")
    print("=" * 60)
    
    data_dir = r"D:\project\ai\ai-gaokao-jobs-china\data"
    filepath = os.path.join(data_dir, "all.json")
    
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📁 文件大小: {os.path.getsize(filepath):,} 字节 ({os.path.getsize(filepath)/1024/1024:.2f} MB)")
        print(f"📄 根结构: 字典，包含 {len(data)} 个键")
        print()
        
        # 1. 基本信息
        print("1️⃣ 基本信息:")
        print("-" * 40)
        print(f"   抓取时间: {data.get('抓取时间', 'N/A')}")
        print(f"   来源: {data.get('来源', 'N/A')}")
        
        # 2. 培养层次列表分析
        education_levels = data.get('培养层次列表', [])
        print(f"\n2️⃣ 培养层次列表分析:")
        print("-" * 40)
        print(f"   包含 {len(education_levels)} 个培养层次")
        
        all_majors = []  # 存储所有专业
        
        for i, level in enumerate(education_levels):
            level_name = level.get('名称', f'未知层次_{i+1}')
            print(f"\n   📌 培养层次 {i+1}: {level_name}")
            
            categories = level.get('门类列表', [])
            print(f"     包含 {len(categories)} 个门类")
            
            if categories:
                # 显示门类名称
                category_names = []
                for cat in categories:
                    if isinstance(cat, dict):
                        category_name = cat.get('门类', cat.get('名称', '未知门类'))
                        category_names.append(category_name)
                
                print(f"     门类列表: {category_names[:5]}")
                if len(category_names) > 5:
                    print(f"     ... 还有 {len(category_names)-5} 个门类")
                
                # 深入分析第一个门类
                first_category = categories[0]
                if isinstance(first_category, dict):
                    first_cat_name = first_category.get('门类', first_category.get('名称', '第一个门类'))
                    print(f"\n     🧪 第一个门类 '{first_cat_name}' 的详细结构:")
                    
                    # 获取门类的所有键
                    cat_keys = list(first_category.keys())
                    print(f"       包含字段: {cat_keys}")
                    
                    # 检查是否有专业类列表
                    if '专业类列表' in first_category:
                        major_classes = first_category['专业类列表']
                        print(f"       专业类数量: {len(major_classes)}")
                        
                        if major_classes and len(major_classes) > 0:
                            first_major_class = major_classes[0]
                            print(f"\n       第一个专业类:")
                            for key, value in first_major_class.items():
                                v_type = type(value).__name__
                                if isinstance(value, str):
                                    print(f"         '{key}': {v_type} = '{value}'")
                                elif isinstance(value, list):
                                    print(f"         '{key}': {v_type} (长度: {len(value)})")
                                    
                                    # 如果是专业列表，显示前几个专业
                                    if key == '专业列表' and value and len(value) > 0:
                                        print(f"           前3个专业:")
                                        for j, major in enumerate(value[:3]):
                                            if isinstance(major, dict):
                                                major_name = major.get('专业名称', f'专业_{j+1}')
                                                print(f"             {j+1}. {major_name}")
                                                
                                                # 保存专业信息
                                                major_info = {
                                                    '培养层次': level_name,
                                                    '门类名称': first_cat_name,
                                                    '专业类': first_major_class.get('专业类', '未知专业类'),
                                                    '专业名称': major_name,
                                                    '专业代码': major.get('专业代码', ''),
                                                    '修业年限': major.get('修业年限', ''),
                                                    '授予学位': major.get('授予学位', '')
                                                }
                                                all_majors.append(major_info)
                                            elif isinstance(major, str):
                                                print(f"             {j+1}. {major}")
                                            else:
                                                print(f"             {j+1}. {type(major).__name__}")
                                    else:
                                        # 如果不是专业列表，尝试显示内容
                                        if value and len(value) > 0:
                                            first_item = value[0]
                                            if isinstance(first_item, dict):
                                                print(f"           包含的键: {list(first_item.keys())[:3]}")
                                else:
                                    print(f"         '{key}': {v_type} = {value}")
                    else:
                        print(f"       没有找到'专业类列表'字段")
        
        # 3. 统计总专业数量
        print(f"\n3️⃣ 总专业数量统计:")
        print("-" * 40)
        
        # 重新遍历计算总专业数
        total_majors_count = 0
        major_details = []
        
        for level in education_levels:
            level_name = level.get('名称', '未知层次')
            categories = level.get('门类列表', [])
            
            for category in categories:
                if isinstance(category, dict):
                    category_name = category.get('门类', category.get('名称', '未知门类'))
                    major_classes = category.get('专业类列表', [])
                    
                    for major_class in major_classes:
                        if isinstance(major_class, dict):
                            major_class_name = major_class.get('专业类', '未知专业类')
                            majors = major_class.get('专业列表', [])
                            
                            total_majors_count += len(majors)
                            
                            # 保存专业详情
                            for major in majors:
                                if isinstance(major, dict):
                                    major_details.append({
                                        '培养层次': level_name,
                                        '门类': category_name,
                                        '专业类': major_class_name,
                                        '专业代码': major.get('专业代码', ''),
                                        '专业名称': major.get('专业名称', '未知专业'),
                                        '修业年限': major.get('修业年限', ''),
                                        '授予学位': major.get('授予学位', ''),
                                        '备注': major.get('备注', '')
                                    })
        
        print(f"   总专业数: {total_majors_count:,}")
        
        if major_details:
            print(f"\n   专业示例 (前5个):")
            for i, major in enumerate(major_details[:5]):
                print(f"     {i+1}. {major['专业名称']} ({major['专业代码']})")
                print(f"         培养层次: {major['培养层次']}, 门类: {major['门类']}")
                print(f"         专业类: {major['专业类']}, 修业年限: {major['修业年限']}")
                print(f"         授予学位: {major['授予学位']}")
        
        # 4. 按培养层次统计专业数
        print(f"\n4️⃣ 按培养层次统计:")
        print("-" * 40)
        
        level_stats = defaultdict(int)
        for major in major_details:
            level_stats[major['培养层次']] += 1
        
        for level, count in level_stats.items():
            print(f"   {level}: {count:,} 个专业")
        
        # 5. 按门类统计专业数
        print(f"\n5️⃣ 按门类统计 (前10个):")
        print("-" * 40)
        
        category_stats = Counter([major['门类'] for major in major_details])
        for category, count in category_stats.most_common(10):
            print(f"   {category}: {count:,} 个专业")
        
        # 6. 按专业类统计
        print(f"\n6️⃣ 按专业类统计 (前10个):")
        print("-" * 40)
        
        major_class_stats = Counter([major['专业类'] for major in major_details])
        for major_class, count in major_class_stats.most_common(10):
            print(f"   {major_class}: {count:,} 个专业")
        
        return {
            'data': data,
            'major_details': major_details,
            'total_majors': total_majors_count
        }
        
    except Exception as e:
        print(f"❌ 分析时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def enhanced_data_json_analysis():
    """增强版 data.json 分析，包含更多统计"""
    print("📈 增强版 data.json 职业数据分析")
    print("=" * 60)
    
    data_dir = r"D:\project\ai\ai-gaokao-jobs-china\data"
    filepath = os.path.join(data_dir, "data.json")
    
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        occupations = data.get('occupations', [])
        print(f"📁 文件大小: {os.path.getsize(filepath):,} 字节")
        print(f"💼 职业数量: {len(occupations)}")
        print()
        
        if not occupations:
            print("❌ 没有职业数据")
            return None
        
        # 1. 职业类别深度分析
        print("1️⃣ 职业类别深度分析:")
        print("-" * 40)
        
        categories = [occ.get('category', '未分类') for occ in occupations]
        category_counts = Counter(categories)
        
        print(f"   共有 {len(category_counts)} 个职业类别:")
        for i, (category, count) in enumerate(category_counts.most_common()):
            percentage = count / len(occupations) * 100
            print(f"   {i+1:2d}. {category:<20} {count:3d} 个 ({percentage:5.1f}%)")
            
            # 显示每个类别中的职业示例
            if i < 5:  # 只显示前5个类别的示例
                examples = [occ.get('title') for occ in occupations 
                          if occ.get('category') == category][:3]
                print(f"       示例: {', '.join(examples)}")
        
        # 2. 就业人数详细分析
        print(f"\n2️⃣ 就业人数详细分析:")
        print("-" * 40)
        
        employment_data = [occ.get('employment_workers', 0) for occ in occupations]
        
        if employment_data:
            # 转换为百万为单位
            employment_millions = [emp / 1000000 for emp in employment_data]
            
            stats = {
                '总和': sum(employment_data),
                '平均': np.mean(employment_data),
                '中位数': np.median(employment_data),
                '最大值': max(employment_data),
                '最小值': min(employment_data),
                '标准差': np.std(employment_data)
            }
            
            print("   基本统计 (单位: 人):")
            for key, value in stats.items():
                if key in ['总和', '最大值']:
                    print(f"     {key}: {value:,.0f}")
                elif key == '标准差':
                    print(f"     {key}: {value:,.0f}")
                else:
                    print(f"     {key}: {value:,.0f}")
            
            # 找出就业人数最多的职业
            print(f"\n   就业人数最多的职业:")
            sorted_by_emp = sorted(occupations, key=lambda x: x.get('employment_workers', 0), reverse=True)
            for i, occ in enumerate(sorted_by_emp[:5]):
                emp = occ.get('employment_workers', 0)
                print(f"     {i+1}. {occ.get('title', '未知')} ({emp/10000:.0f}万人) - {occ.get('category', '未分类')}")
        
        # 3. 工资水平深入分析
        print(f"\n3️⃣ 工资水平深入分析:")
        print("-" * 40)
        
        salary_data = []
        salary_numeric = []  # 用于存储数字化的工资数据
        
        for occ in occupations:
            salary_str = occ.get('avgSalary', '')
            if isinstance(salary_str, str) and '万' in salary_str:
                # 提取数字，如"1.5万-3.5万"
                numbers = re.findall(r'\d+\.?\d*', salary_str)
                if len(numbers) >= 2:
                    low, high = float(numbers[0]), float(numbers[1])
                    salary_data.append((low, high))
                    salary_numeric.append((low + high) / 2)  # 取中位数
        
        if salary_data:
            avg_low = np.mean([s[0] for s in salary_data])
            avg_high = np.mean([s[1] for s in salary_data])
            avg_mid = np.mean(salary_numeric)
            
            print(f"   平均工资范围: {avg_low:.1f}万 - {avg_high:.1f}万")
            print(f"   平均工资中位数: {avg_mid:.1f}万")
            
            # 按类别分析工资
            print(f"\n   按类别平均工资 (前5个类别):")
            category_salaries = defaultdict(list)
            
            for occ in occupations:
                category = occ.get('category', '未分类')
                salary_str = occ.get('avgSalary', '')
                
                if isinstance(salary_str, str) and '万' in salary_str:
                    numbers = re.findall(r'\d+\.?\d*', salary_str)
                    if len(numbers) >= 2:
                        low, high = float(numbers[0]), float(numbers[1])
                        category_salaries[category].append((low + high) / 2)
            
            # 计算每个类别的平均工资
            avg_category_salaries = {}
            for category, salaries in category_salaries.items():
                if salaries:
                    avg_category_salaries[category] = np.mean(salaries)
            
            # 按平均工资排序
            sorted_categories = sorted(avg_category_salaries.items(), key=lambda x: x[1], reverse=True)
            for i, (category, avg_salary) in enumerate(sorted_categories[:5]):
                count = len(category_salaries[category])
                print(f"     {i+1}. {category}: {avg_salary:.1f}万 ({count}个样本)")
        
        # 4. 曝光度与工资相关性分析
        print(f"\n4️⃣ 曝光度与工资相关性分析:")
        print("-" * 40)
        
        exposure_data = []
        salary_mid_data = []
        
        for occ in occupations:
            exposure = occ.get('exposure', 0)
            salary_str = occ.get('avgSalary', '')
            
            if isinstance(salary_str, str) and '万' in salary_str:
                numbers = re.findall(r'\d+\.?\d*', salary_str)
                if len(numbers) >= 2:
                    low, high = float(numbers[0]), float(numbers[1])
                    salary_mid = (low + high) / 2
                    exposure_data.append(exposure)
                    salary_mid_data.append(salary_mid)
        
        if exposure_data and salary_mid_data:
            # 计算相关性
            if len(exposure_data) > 1:
                correlation = np.corrcoef(exposure_data, salary_mid_data)[0, 1]
                print(f"   曝光度与工资的相关性: {correlation:.3f}")
                
                if correlation > 0.3:
                    print("   💡 提示: 曝光度与工资呈正相关")
                elif correlation < -0.3:
                    print("   💡 提示: 曝光度与工资呈负相关")
                else:
                    print("   💡 提示: 曝光度与工资相关性较弱")
            
            # 按曝光度分组统计平均工资
            print(f"\n   按曝光度分组的平均工资:")
            exposure_groups = defaultdict(list)
            
            for exp, salary in zip(exposure_data, salary_mid_data):
                exposure_groups[exp].append(salary)
            
            for exp in sorted(exposure_groups.keys()):
                avg_salary = np.mean(exposure_groups[exp])
                count = len(exposure_groups[exp])
                print(f"     曝光度{exp}: {avg_salary:.1f}万 ({count}个样本)")
        
        # 5. 高亮职业详细分析
        print(f"\n5️⃣ 高亮职业详细分析:")
        print("-" * 40)
        
        highlighted_occ = [occ for occ in occupations if occ.get('highlighted') == True]
        
        print(f"   高亮职业数量: {len(highlighted_occ)} 个 ({len(highlighted_occ)/len(occupations)*100:.1f}%)")
        
        if highlighted_occ:
            print(f"\n   ⭐ 高亮职业列表:")
            for i, occ in enumerate(highlighted_occ):
                title = occ.get('title', '未知')
                category = occ.get('category', '未分类')
                salary = occ.get('avgSalary', 'N/A')
                exposure = occ.get('exposure', 0)
                
                print(f"     {i+1}. ★ {title}")
                print(f"         类别: {category}, 工资: {salary}, 曝光度: {exposure}")
                
                # 显示描述摘要
                detail = occ.get('detail', '')
                if detail and len(detail) > 50:
                    print(f"         描述: {detail[:50]}...")
                elif detail:
                    print(f"         描述: {detail}")
            
            # 高亮职业的统计
            print(f"\n   📊 高亮职业统计:")
            highlighted_categories = Counter([occ.get('category', '未分类') for occ in highlighted_occ])
            
            for category, count in highlighted_categories.most_common():
                percentage = count / len(highlighted_occ) * 100
                print(f"     {category}: {count} 个 ({percentage:.0f}%)")
        
        # 6. 数据质量检查
        print(f"\n6️⃣ 数据质量检查:")
        print("-" * 40)
        
        missing_fields = defaultdict(int)
        for occ in occupations:
            for field in ['title', 'category', 'employment_workers', 'exposure', 
                         'highlighted', 'avgSalary', 'detail', 'source_url']:
                if field not in occ or occ[field] in ['', None]:
                    missing_fields[field] += 1
        
        print("   字段缺失统计:")
        for field, count in missing_fields.items():
            if count > 0:
                percentage = count / len(occupations) * 100
                print(f"     {field}: {count} 个缺失 ({percentage:.1f}%)")
            else:
                print(f"     {field}: 完整")
        
        # 7. 数据导出准备
        print(f"\n7️⃣ 数据导出准备:")
        print("-" * 40)
        
        # 创建DataFrame
        df = pd.DataFrame(occupations)
        
        # 添加计算字段
        df['工资中位数(万)'] = None
        for idx, row in df.iterrows():
            salary_str = row.get('avgSalary', '')
            if isinstance(salary_str, str) and '万' in salary_str:
                numbers = re.findall(r'\d+\.?\d*', salary_str)
                if len(numbers) >= 2:
                    low, high = float(numbers[0]), float(numbers[1])
                    df.at[idx, '工资中位数(万)'] = (low + high) / 2
        
        print(f"   DataFrame形状: {df.shape}")
        print(f"   列: {list(df.columns)}")
        print(f"   数据类型:")
        for col in df.columns:
            non_null = df[col].count()
            null_count = df[col].isnull().sum()
            dtype = df[col].dtype
            print(f"     {col}: {dtype}, 非空: {non_null}, 空值: {null_count}")
        
        return {
            'data': data,
            'dataframe': df,
            'occupations': occupations
        }
        
    except Exception as e:
        print(f"❌ 分析时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def export_enhanced_data():
    """导出增强版数据"""
    print("🚀 导出增强版数据分析结果")
    print("=" * 60)
    
    data_dir = r"D:\project\ai\ai-gaokao-jobs-china\data"
    output_dir = os.path.join(data_dir, "..", "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 分析 all.json
    print("\n1️⃣ 分析 all.json 文件...")
    all_result = fix_all_json_analysis()
    
    if all_result and 'major_details' in all_result:
        # 导出专业数据
        majors_df = pd.DataFrame(all_result['major_details'])
        majors_output = os.path.join(output_dir, "education_majors_detailed.csv")
        majors_df.to_csv(majors_output, index=False, encoding='utf-8-sig')
        print(f"   ✅ 导出专业数据: {majors_output} ({len(majors_df)} 条记录)")
        
        # 生成专业统计报告
        stats_output = os.path.join(output_dir, "education_stats.txt")
        with open(stats_output, 'w', encoding='utf-8') as f:
            f.write("教育专业数据统计报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"总专业数: {len(majors_df):,}\n\n")
            
            f.write("按培养层次统计:\n")
            level_stats = majors_df['培养层次'].value_counts()
            for level, count in level_stats.items():
                f.write(f"  {level}: {count:,}\n")
            
            f.write("\n按门类统计 (前20个):\n")
            category_stats = majors_df['门类'].value_counts().head(20)
            for category, count in category_stats.items():
                f.write(f"  {category}: {count:,}\n")
        
        print(f"   📊 生成统计报告: {stats_output}")
    
    # 2. 分析 data.json
    print("\n2️⃣ 分析 data.json 文件...")
    data_result = enhanced_data_json_analysis()
    
    if data_result and 'dataframe' in data_result:
        df = data_result['dataframe']
        
        # 导出职业数据
        occ_output = os.path.join(output_dir, "occupations_enhanced.csv")
        df.to_csv(occ_output, index=False, encoding='utf-8-sig')
        print(f"   ✅ 导出职业数据: {occ_output} ({len(df)} 条记录)")
        
        # 生成职业统计报告
        occ_stats_output = os.path.join(output_dir, "occupation_stats.txt")
        with open(occ_stats_output, 'w', encoding='utf-8') as f:
            f.write("职业数据分析报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"总职业数: {len(df):,}\n\n")
            
            f.write("按类别统计:\n")
            category_stats = df['category'].value_counts()
            for category, count in category_stats.items():
                percentage = count / len(df) * 100
                f.write(f"  {category}: {count:,} ({percentage:.1f}%)\n")
            
            f.write("\n高亮职业:\n")
            highlighted = df[df['highlighted'] == True]
            for _, row in highlighted.iterrows():
                f.write(f"  ★ {row['title']} - {row['category']}\n")
            
            f.write(f"\n平均曝光度: {df['exposure'].mean():.1f}\n")
            f.write(f"平均就业人数: {df['employment_workers'].mean():,.0f}\n")
        
        print(f"   📊 生成职业统计报告: {occ_stats_output}")
        
        # 生成分析图表数据
        chart_data_output = os.path.join(output_dir, "chart_data.json")
        chart_data = {
            "categories": df['category'].value_counts().head(10).to_dict(),
            "employment_distribution": {
                "<1万": len(df[df['employment_workers'] < 10000]),
                "1-5万": len(df[(df['employment_workers'] >= 10000) & (df['employment_workers'] < 50000)]),
                "5-10万": len(df[(df['employment_workers'] >= 50000) & (df['employment_workers'] < 100000)]),
                "10-50万": len(df[(df['employment_workers'] >= 100000) & (df['employment_workers'] < 500000)]),
                "50-100万": len(df[(df['employment_workers'] >= 500000) & (df['employment_workers'] < 1000000)]),
                ">100万": len(df[df['employment_workers'] >= 1000000])
            }
        }
        
        with open(chart_data_output, 'w', encoding='utf-8') as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)
        
        print(f"   📈 生成图表数据: {chart_data_output}")
    
    print(f"\n🎉 所有数据已导出到: {output_dir}")

def main():
    """主函数"""
    while True:
        print("\n" + "=" * 60)
        print("🔧 修复版JSON数据分析工具")
        print("=" * 60)
        print("1. 🔬 修复 all.json 分析 (正确提取专业数据)")
        print("2. 📈 增强 data.json 分析 (更多统计)")
        print("3. 🚀 导出所有增强数据")
        print("4. 🏁 退出")
        print("-" * 60)
        
        choice = input("请选择操作 (1-4): ").strip()
        
        if choice == "1":
            fix_all_json_analysis()
        elif choice == "2":
            enhanced_data_json_analysis()
        elif choice == "3":
            export_enhanced_data()
        elif choice == "4":
            print("👋 退出程序")
            break
        else:
            print("❌ 无效选择，请重新输入")
        
        if choice in ["1", "2", "3"]:
            input("\n按Enter键继续...")

if __name__ == "__main__":
    main()