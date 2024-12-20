import os
import numpy as np
import base64
import textwrap
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.colors import ListedColormap
matplotlib.use('Agg')
import seaborn as sns

from io import BytesIO
from datetime import datetime
from flask import Blueprint, request, session, render_template, send_file

from utils.auth_utils import login_required
from utils.project_utils import get_project_folder
from utils.load_df import load_df
from utils.info_tables import gerar_estatisticas_tabela,gerar_resumo_tabela
exploratory_analysis_routes = Blueprint('exploratory_analysis_routes', __name__)



def adicionar_space(df):
    if df.shape[1] > 0:  # Garante que há ao menos uma coluna
        df.iloc[:, 0] = df.iloc[:, 0].apply(
            lambda x: x.replace('.', '. ') if isinstance(x, str) else x
        )
    return df

@exploratory_analysis_routes.route('/criar_tabela_continuo', methods=['GET'])
@login_required
def criar_tabela_continuo_route():
    temp_folder = get_project_folder('temp')
    colunas_selecionadas = request.args.getlist('colunas')
    df = load_df(temp_folder)
    tabela_continua = gerar_estatisticas_tabela(df[colunas_selecionadas])
    tabela_continua = adicionar_space(tabela_continua)
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()


    file_root, _ = os.path.splitext(session['selected_file'])
    tabela_continua.to_csv(os.path.join(temp_folder, file_root + "_exploratory_table.csv"),index=False)

    table_html = tabela_continua.to_html(classes='table table-striped')

    # Manually insert <thead> and <tbody>
    table_html = table_html.replace('<table ', '<table class="table table-striped" ')
    table_html = table_html.replace('<thead>', '<thead class="thead-light">')
    table_html = table_html.replace('<tbody>', '<tbody class="table-body">')
    session['table_html']=table_html

    # Verifique se deve usar o template base_analysis
    use_base_template = request.args.get('use_base_template', 'false').lower() == 'true'

    # Escolha o template
    template_to_render = 'base_analysis.html' if use_base_template else 'exploratory_analysis.html'

    return render_template(template_to_render, uploaded_files=session['sheet_names'], column_names=column_names, table=table_html,image=None, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@exploratory_analysis_routes.route('/data_dict', methods=['GET'])
@login_required
def criar_data_dict_route():
    temp_folder = get_project_folder('temp')
    colunas_selecionadas = request.args.getlist('colunas')
    df = load_df(temp_folder)
    data_dict = gerar_resumo_tabela(df[colunas_selecionadas])
    data_dict = adicionar_space(data_dict)
    column_names=None
    if(df is not None):
        column_names = df.columns.tolist()


    file_root, _ = os.path.splitext(session['selected_file'])
    data_dict.to_csv(os.path.join(temp_folder, file_root + "_exploratory_table.csv"),index=False)

    table_html = data_dict.to_html(classes='table table-striped')

    # Manually insert <thead> and <tbody>
    table_html = table_html.replace('<table ', '<table class="table table-striped" ')
    table_html = table_html.replace('<thead>', '<thead class="thead-light">')
    table_html = table_html.replace('<tbody>', '<tbody class="table-body">')
    session['table_html']=table_html

    # Verifique se deve usar o template base_analysis
    use_base_template = request.args.get('use_base_template', 'false').lower() == 'true'

    # Escolha o template
    template_to_render = 'base_analysis.html' if use_base_template else 'exploratory_analysis.html'

    return render_template(template_to_render, uploaded_files=session['sheet_names'], column_names=column_names, table=table_html,image=None, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@exploratory_analysis_routes.route('/download_csv', methods=['GET'])
@login_required
def download_csv():
    temp_folder = get_project_folder('temp')
    file_root, _ = os.path.splitext(session['selected_file'])
    temp_filename = os.path.join(temp_folder, file_root + "_exploratory_table.csv")
    if temp_filename and os.path.exists(temp_filename):
        return send_file( temp_filename, as_attachment=True, download_name=file_root + "_exploratory_table.csv", mimetype='text/csv')
    return "No table to download", 400

@exploratory_analysis_routes.route('/completude_graph', methods=['GET'])
@login_required
def completude_graph():
    temp_folder = get_project_folder('temp')
    colunas_selecionadas = request.args.getlist('colunas')
    df = load_df(temp_folder)
    column_names = df.columns.tolist() if df is not None else None

    valores_vazios = ["", "NA", "null", "N/A", "undefined","nan"]  # Adicione aqui os valores que você quer tratar como NaN
    df=df.replace(valores_vazios, np.nan)
    plt.figure(figsize=(10, 6))  # Ajuste o tamanho conforme necessário
    sns.heatmap(
        df[colunas_selecionadas].transpose().isnull(),
        cbar=False,
        cmap=ListedColormap(["purple", "yellow"]),
        linecolor='white',
        vmin=0,  # Define o limite inferior como 0
        vmax=1   # Define o limite superior como 1
    )

    plt.xlabel(f"{df[colunas_selecionadas].shape[0]} linhas")
    plt.ylabel(f"{df[colunas_selecionadas].shape[1]} colunas")

    # Ajuste os nomes das colunas para não cortarem
    ax = plt.gca()
    yticklabels = df[colunas_selecionadas].columns

    # Dividir nomes longos em múltiplas linhas
    wrapped_labels = [
        "\n".join(textwrap.wrap(label, width=20)) for label in yticklabels
    ]
    ax.set_yticklabels(wrapped_labels, fontsize=8, rotation=0)  # Ajuste o tamanho e a rotação conforme necessário

    # Ajuste do layout para evitar cortes
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
    
    file_root, _ = os.path.splitext(session['selected_file'])
    image_filename = os.path.join(temp_folder, str(datetime.now().strftime("%d%m%Y%H%M%S")) + "_completude_graph.png")
    session['image_filename'] = image_filename
    with open(image_filename, 'wb') as f:
        f.write(img.getvalue())

    # Verifique se deve usar o template base_analysis
    use_base_template = request.args.get('use_base_template', 'false').lower() == 'true'

    # Escolha o template
    template_to_render = 'base_analysis.html' if use_base_template else 'exploratory_analysis.html'

    return render_template(template_to_render, uploaded_files=session['sheet_names'], column_names=column_names, table=None, image=img_base64, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@exploratory_analysis_routes.route('/plot_graph', methods=['POST'])
@login_required
def plot_graph():
    temp_folder = get_project_folder('temp')
    x_column = request.form['x_column']
    y_column = request.form['y_column']
    chart_type = request.form['chart_type']
    image_size = request.form['image_size'].split('x')
    width, height = int(image_size[0]), int(image_size[1])
    point_color = request.form['point_color']
    
    # Obter título personalizado, se fornecido
    custom_title = request.form.get('custom_title', '')
    
    # Obter as unidades de medida para X e Y, se fornecidas
    x_unit = request.form.get('x_unit', '')
    y_unit = request.form.get('y_unit', '')

    df = load_df(temp_folder)
    column_names = df.columns.tolist() if df is not None else None
    x_min, x_max = min(df[x_column]), max(df[x_column])
    plt.figure(figsize=(width, height))

    # Definir título com base no valor personalizado ou título padrão
    title = custom_title if custom_title else f'Gráfico de {chart_type.capitalize()} {y_column} vs {x_column}'

    # Verifica o tipo de gráfico e plota
    if chart_type == 'line':
        plt.plot(df[x_column], df[y_column], marker='o', color=point_color, linestyle='-')
        plt.xlim(x_min, x_max)
        plt.title(title)
        plt.xlabel(f"{x_column} ({x_unit})" if x_unit else x_column)
        plt.ylabel(f"{y_column} ({y_unit})" if y_unit else y_column)
    elif chart_type == 'scatter':
        plt.scatter(df[x_column], df[y_column], color=point_color)
        plt.xlim(x_min, x_max)
        plt.title(title)
        plt.xlabel(f"{x_column} ({x_unit})" if x_unit else x_column)
        plt.ylabel(f"{y_column} ({y_unit})" if y_unit else y_column)
    elif chart_type == 'bar':
        plt.bar(df[x_column], df[y_column], color=point_color)
        plt.xlim(x_min, x_max)
        plt.title(title)
        plt.xlabel(f"{x_column} ({x_unit})" if x_unit else x_column)
        plt.ylabel(f"{y_column} ({y_unit})" if y_unit else y_column)
    elif chart_type == 'histogram':
        plt.title(title)
        plt.xlim(x_min, x_max)
        plt.hist(df[x_column], bins=30, color=point_color)
        plt.ylabel(f"{x_column} ({x_unit})" if x_unit else x_column)

    plt.grid(True)
    plt.tight_layout()

    img = BytesIO()
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    file_root, _ = os.path.splitext(session['selected_file'])
    image_filename = os.path.join(temp_folder, str(datetime.now().strftime("%d%m%Y%H%M%S")) + str(chart_type) + "_plot.png")
    session['image_filename'] = image_filename
    with open(image_filename, 'wb') as f:
        f.write(img.getvalue())
    
    return render_template('exploratory_analysis.html', uploaded_files=session['sheet_names'], column_names=column_names, table=None, image=img_base64, selected_file=session["selected_file"], selected_sheet=session["selected_sheet"])

@exploratory_analysis_routes.route('/download_plot', methods=['GET'])
@login_required
def download_plot():
    file_root, _ = os.path.splitext(session['selected_file'])
    temp_filename = session['image_filename']
    if temp_filename and os.path.exists(temp_filename):
        return send_file( temp_filename, as_attachment=True, download_name=file_root + "_plot.png", mimetype='png')
    return "No plot to download", 400
