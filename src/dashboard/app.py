"""
UCCNCT Dashboard - Plateforme de Veille Sociale Multi-Sources
"""

import streamlit as st
import pandas as pd
import boto3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import s3fs


st.set_page_config(
    page_title="UCCNCT - Veille Sociale",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)


AWS_REGION = "us-east-1"
RAW_BUCKET = "uccnt-ef98cc0f-raw"
PROCESSED_BUCKET = "uccnt-ef98cc0f-processed"
CURATED_BUCKET = "uccnt-ef98cc0f-curated"


SOURCE_COLORS = {
    "bluesky": "#0085FF",
    "nostr": "#8B5CF6",
    "hackernews": "#FF6600",
    "stackoverflow": "#F48024",
    "rss": "#2E7D32"
}


@st.cache_resource
def get_s3_client():
    return boto3.client('s3', region_name=AWS_REGION)

@st.cache_data(ttl=300)
def load_parquet(bucket, path):
    """Charge un fichier ou un dossier Parquet depuis S3"""
    try:
        clean_path = path.rstrip('/')
        full_path = f"s3://{bucket}/{clean_path}"

        df = pd.read_parquet(full_path, engine='pyarrow')
        return df
    except Exception as e:
        try:
            full_path = f"s3://{bucket}/{path}"
            df = pd.read_parquet(full_path, engine='pyarrow')
            return df
        except:
            st.error(f"Erreur chargement {path}: {e}")
            return pd.DataFrame()

@st.cache_data(ttl=300)
def format_bytes(size_bytes):
    """Formatte une taille en octets de manière lisible (B, KB, MB, GB, etc.)"""
    if size_bytes == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"

@st.cache_data(ttl=300)
def get_bucket_stats(bucket_name):
    """Statistiques d'un bucket S3 (compte TOUS les fichiers avec pagination)"""
    try:
        s3 = get_s3_client()
        count = 0
        size = 0
        continuation_token = None

        while True:
            if continuation_token:
                response = s3.list_objects_v2(
                    Bucket=bucket_name,
                    MaxKeys=1000,
                    ContinuationToken=continuation_token
                )
            else:
                response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1000)

            count += response.get('KeyCount', 0)
            size += sum(obj.get('Size', 0) for obj in response.get('Contents', []))

            if not response.get('IsTruncated', False):
                break
            continuation_token = response.get('NextContinuationToken')

        return count, size
    except:
        return 0, 0

@st.cache_data(ttl=60)
def load_curated_data():
    """Charge toutes les donnees curated"""
    data = {}

    try:
        data['global_summary'] = load_parquet(CURATED_BUCKET, "reports/global_summary/")
    except:
        data['global_summary'] = pd.DataFrame()

    try:
        data['source_summary'] = load_parquet(CURATED_BUCKET, "reports/source_summary/")
    except:
        data['source_summary'] = pd.DataFrame()

    try:
        data['volume'] = load_parquet(CURATED_BUCKET, "analytics/volume_by_source/")
    except:
        data['volume'] = pd.DataFrame()

    try:
        data['keywords'] = load_parquet(CURATED_BUCKET, "trends/keywords/")
    except:
        data['keywords'] = pd.DataFrame()

    try:
        data['categories'] = load_parquet(CURATED_BUCKET, "trends/categories/")
    except:
        data['categories'] = pd.DataFrame()

    try:
        data['hourly'] = load_parquet(CURATED_BUCKET, "analytics/hourly_activity/")
    except:
        data['hourly'] = pd.DataFrame()

    try:
        data['remapping'] = load_parquet(CURATED_BUCKET, "analytics/remapping_stats/")
    except:
        data['remapping'] = pd.DataFrame()

    try:
        data['volume_week'] = load_parquet(CURATED_BUCKET, "analytics/volume_by_week/")
    except:
        data['volume_week'] = pd.DataFrame()

    try:
        data['volume_month'] = load_parquet(CURATED_BUCKET, "analytics/volume_by_month/")
    except:
        data['volume_month'] = pd.DataFrame()

    try:
        data['growth'] = load_parquet(CURATED_BUCKET, "analytics/growth_rate/")
    except:
        data['growth'] = pd.DataFrame()

    try:
        data['content_stats'] = load_parquet(CURATED_BUCKET, "analytics/content_stats/")
    except:
        data['content_stats'] = pd.DataFrame()

    try:
        data['cross_keywords'] = load_parquet(CURATED_BUCKET, "trends/cross_source_keywords/")
    except:
        data['cross_keywords'] = pd.DataFrame()

    try:
        data['keywords_by_source'] = load_parquet(CURATED_BUCKET, "trends/keywords_by_source/")
    except:
        data['keywords_by_source'] = pd.DataFrame()

    try:
        data['extended_summary'] = load_parquet(CURATED_BUCKET, "reports/extended_summary/")
    except:
        data['extended_summary'] = pd.DataFrame()

    return data


with st.sidebar:
    st.title("UCCNCT")
    st.caption("Veille Sociale Multi-Sources")

    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["Vue d'ensemble", "Tendances", "Volume & Sources", "Croissance", "Activite", "Requetes SQL", "Explorateur S3"],
        index=0
    )

    st.markdown("---")


    if st.button("Actualiser les donnees"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")


    st.subheader("Buckets S3")
    r_count, r_size = get_bucket_stats(RAW_BUCKET)
    p_count, p_size = get_bucket_stats(PROCESSED_BUCKET)
    c_count, c_size = get_bucket_stats(CURATED_BUCKET)

    st.caption(f"Raw: {r_count:,} fichiers ({format_bytes(r_size)})")
    st.caption(f"Processed: {p_count:,} fichiers ({format_bytes(p_size)})")
    st.caption(f"Curated: {c_count:,} fichiers ({format_bytes(c_size)})")

    st.markdown("---")
    st.caption("Sources: Bluesky, Nostr, HackerNews, StackOverflow, RSS")

data = load_curated_data()

if page == "Vue d'ensemble":
    st.title("Vue d'ensemble")
    st.caption("Metriques globales du Data Lake UCCNCT")

    col1, col2, col3, col4 = st.columns(4)

    if not data['global_summary'].empty:
        gs = data['global_summary'].iloc[0]
        col1.metric("Total Posts", f"{int(gs.get('total_posts', 0)):,}")
        col2.metric("Sources Actives", int(gs.get('active_sources', 0)))
        col3.metric("Posts avec Keywords", f"{int(gs.get('total_with_keywords', 0)):,}")
        col4.metric("Posts Remappes", f"{int(gs.get('total_remapped', 0)):,}")
    else:
        col1.metric("Total Posts", "N/A")
        col2.metric("Sources Actives", "N/A")
        col3.metric("Posts avec Keywords", "N/A")
        col4.metric("Posts Remappes", "N/A")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Repartition par Source")
        if not data['source_summary'].empty:
            fig_pie = px.pie(
                data['source_summary'],
                values='total_posts',
                names='source',
                color='source',
                color_discrete_map=SOURCE_COLORS,
                hole=0.4
            )
            fig_pie.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Pas de donnees de repartition")

    with col_right:
        st.subheader("Volume par Source")
        if not data['source_summary'].empty:
            fig_bar = px.bar(
                data['source_summary'].sort_values('total_posts', ascending=True),
                x='total_posts',
                y='source',
                orientation='h',
                color='source',
                color_discrete_map=SOURCE_COLORS
            )
            fig_bar.update_layout(showlegend=False, yaxis_title="", xaxis_title="Nombre de posts")
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Pas de donnees de volume")

    st.markdown("---")

    st.subheader("Top 10 Keywords")
    if not data['keywords'].empty:
        top_kw = data['keywords'].nlargest(10, 'mentions')
        fig_kw = px.bar(
            top_kw,
            x='mentions',
            y='keyword',
            orientation='h',
            color='mentions',
            color_continuous_scale='Blues'
        )
        fig_kw.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False,
            yaxis_title="",
            xaxis_title="Mentions"
        )
        st.plotly_chart(fig_kw, use_container_width=True)
    else:
        st.info("Pas de donnees de keywords")

elif page == "Tendances":
    st.title("Tendances")
    st.caption("Mots-cles et categories en vogue")

    tab1, tab2, tab3 = st.tabs(["Keywords", "Categories", "Cross-Source"])

    with tab1:
        if not data['keywords'].empty:
            if 'date' in data['keywords'].columns:
                dates = pd.to_datetime(data['keywords']['date']).dt.date.unique()
                selected_date = st.selectbox("Date", sorted(dates, reverse=True))
                df_filtered = data['keywords'][pd.to_datetime(data['keywords']['date']).dt.date == selected_date]
            else:
                df_filtered = data['keywords']

            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("Top 20 Keywords")
                top_20 = df_filtered.nlargest(20, 'mentions')
                fig = px.bar(
                    top_20,
                    x='mentions',
                    y='keyword',
                    orientation='h',
                    color='sources_count',
                    color_continuous_scale='Viridis',
                    labels={'sources_count': 'Sources'}
                )
                fig.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    height=600
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("Tableau")
                st.dataframe(
                    df_filtered[['keyword', 'mentions', 'sources_count']].head(30),
                    hide_index=True,
                    use_container_width=True
                )
        else:
            st.info("Pas de donnees de keywords")

    with tab2:
        if not data['categories'].empty:
            st.subheader("Categories")
            fig_cat = px.treemap(
                data['categories'].nlargest(20, 'mentions'),
                path=['category'],
                values='mentions',
                color='mentions',
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_cat, use_container_width=True)

            st.dataframe(
                data['categories'][['category', 'mentions', 'sources_count']].head(20),
                hide_index=True
            )
        else:
            st.info("Pas de donnees de categories")

    with tab3:
        st.subheader("Keywords Cross-Source")
        st.caption("Keywords presents sur plusieurs sources (indicateur de viralite)")

        if not data['cross_keywords'].empty:
            df_cross = data['cross_keywords'].copy()

            col1, col2 = st.columns([2, 1])

            with col1:
                top_viral = df_cross.nlargest(20, 'total_mentions')
                fig_viral = px.bar(
                    top_viral,
                    x='total_mentions',
                    y='keyword',
                    orientation='h',
                    color='sources_count',
                    color_continuous_scale='RdYlGn',
                    title="Top 20 Keywords Multi-Sources"
                )
                fig_viral.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
                st.plotly_chart(fig_viral, use_container_width=True)

            with col2:
                viral_count = df_cross[df_cross['is_viral'] == True].shape[0] if 'is_viral' in df_cross.columns else 0
                total_cross = len(df_cross)

                st.metric("Keywords viraux (3+ sources)", viral_count)
                st.metric("Keywords multi-sources (2+)", total_cross)

                st.markdown("---")
                st.markdown("**Keywords viraux:**")
                if 'is_viral' in df_cross.columns:
                    viral_kw = df_cross[df_cross['is_viral'] == True]['keyword'].head(10).tolist()
                    for kw in viral_kw:
                        st.write(f"- {kw}")

            st.subheader("Tableau complet")
            display_cols = ['keyword', 'total_mentions', 'sources_count']
            if 'is_viral' in df_cross.columns:
                display_cols.append('is_viral')
            st.dataframe(df_cross[display_cols].head(50), hide_index=True, use_container_width=True)
        else:
            st.info("Pas de donnees cross-source - Relancez le job d'agregation")

elif page == "Volume & Sources":
    st.title("Volume & Sources")
    st.caption("Evolution et comparaison des sources")

    if not data['volume'].empty:
        st.subheader("Evolution du volume")

        df_vol = data['volume'].copy()
        if 'date' in df_vol.columns:
            df_vol['date'] = pd.to_datetime(df_vol['date'])

            fig_line = px.line(
                df_vol,
                x='date',
                y='total_posts',
                color='source',
                color_discrete_map=SOURCE_COLORS,
                markers=True
            )
            fig_line.update_layout(
                xaxis_title="Date",
                yaxis_title="Nombre de posts",
                legend_title="Source"
            )
            st.plotly_chart(fig_line, use_container_width=True)

        st.subheader("Comparaison par Source")

        col1, col2 = st.columns(2)

        with col1:
            total_by_source = df_vol.groupby('source')['total_posts'].sum().reset_index()
            fig_total = px.bar(
                total_by_source,
                x='source',
                y='total_posts',
                color='source',
                color_discrete_map=SOURCE_COLORS,
                title="Total des posts par source"
            )
            fig_total.update_layout(showlegend=False)
            st.plotly_chart(fig_total, use_container_width=True)

        with col2:
            st.empty()
            st.info("Visualisation des posts uniques désactivée")

        st.subheader("Donnees detaillees")
        st.dataframe(df_vol, hide_index=True, use_container_width=True)
    else:
        st.info("Pas de donnees de volume")

elif page == "Croissance":
    st.title("Croissance & KPIs")
    st.caption("Indicateurs de performance et evolution")

    tab1, tab2, tab3, tab4 = st.tabs(["Par Semaine", "Par Mois", "Taux de Croissance", "Contenu"])

    with tab1:
        st.subheader("Volume par Semaine")
        if not data['volume_week'].empty:
            df_week = data['volume_week'].copy()

            fig_week = px.bar(
                df_week,
                x='year_week',
                y='total_posts',
                color='source',
                color_discrete_map=SOURCE_COLORS,
                barmode='group',
                title="Posts par semaine et par source"
            )
            fig_week.update_layout(xaxis_title="Semaine", yaxis_title="Nombre de posts")
            st.plotly_chart(fig_week, use_container_width=True)

            st.dataframe(
                df_week[['year_week', 'source', 'total_posts']].sort_values(['year_week', 'source'], ascending=[False, True]),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Pas de donnees hebdomadaires - Relancez le job d'agregation")

    with tab2:
        st.subheader("Volume par Mois")
        if not data['volume_month'].empty:
            df_month = data['volume_month'].copy()

            fig_month = px.bar(
                df_month,
                x='year_month',
                y='total_posts',
                color='source',
                color_discrete_map=SOURCE_COLORS,
                barmode='stack',
                title="Posts par mois (empile)"
            )
            fig_month.update_layout(xaxis_title="Mois", yaxis_title="Nombre de posts")
            st.plotly_chart(fig_month, use_container_width=True)

            fig_month_line = px.line(
                df_month,
                x='year_month',
                y='total_posts',
                color='source',
                color_discrete_map=SOURCE_COLORS,
                markers=True,
                title="Evolution mensuelle par source"
            )
            st.plotly_chart(fig_month_line, use_container_width=True)

            st.dataframe(df_month[['year_month', 'source', 'total_posts']], hide_index=True, use_container_width=True)
        else:
            st.info("Pas de donnees mensuelles - Relancez le job d'agregation")

    with tab3:
        st.subheader("Taux de Croissance Jour/Jour")
        if not data['growth'].empty:
            df_growth = data['growth'].copy()
            df_growth['date'] = pd.to_datetime(df_growth['date'])

            sources = df_growth['source'].unique().tolist()
            selected_source = st.selectbox("Source", ["Toutes"] + sources)

            if selected_source != "Toutes":
                df_filtered = df_growth[df_growth['source'] == selected_source]
            else:
                df_filtered = df_growth

            fig_growth = px.line(
                df_filtered,
                x='date',
                y='growth_pct',
                color='source',
                color_discrete_map=SOURCE_COLORS,
                title="Taux de croissance quotidien (%)",
                markers=True
            )
            fig_growth.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_growth.update_layout(yaxis_title="Croissance (%)", xaxis_title="Date")
            st.plotly_chart(fig_growth, use_container_width=True)

            col1, col2, col3 = st.columns(3)

            if 'growth_pct' in df_filtered.columns:
                avg_growth = df_filtered['growth_pct'].mean()
                max_growth = df_filtered['growth_pct'].max()
                min_growth = df_filtered['growth_pct'].min()

                col1.metric("Croissance moyenne", f"{avg_growth:.1f}%" if pd.notna(avg_growth) else "N/A")
                col2.metric("Max croissance", f"{max_growth:.1f}%" if pd.notna(max_growth) else "N/A")
                col3.metric("Min croissance", f"{min_growth:.1f}%" if pd.notna(min_growth) else "N/A")

            st.dataframe(
                df_filtered[['date', 'source', 'total_posts', 'prev_day_posts', 'growth_pct', 'growth_abs']].sort_values('date', ascending=False),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("Pas de donnees de croissance - Relancez le job d'agregation")

    with tab4:
        st.subheader("Statistiques de Contenu")
        if not data['content_stats'].empty:
            df_content = data['content_stats'].copy()
            df_content['date'] = pd.to_datetime(df_content['date'])

            col1, col2 = st.columns(2)

            with col1:
                avg_by_source = df_content.groupby('source')['avg_length'].mean().reset_index()
                fig_len = px.bar(
                    avg_by_source,
                    x='source',
                    y='avg_length',
                    color='source',
                    color_discrete_map=SOURCE_COLORS,
                    title="Longueur moyenne des posts (caracteres)"
                )
                fig_len.update_layout(showlegend=False)
                st.plotly_chart(fig_len, use_container_width=True)

            with col2:
                totals = df_content.groupby('source').agg({
                    'long_posts': 'sum',
                    'short_posts': 'sum'
                }).reset_index()
                totals_melted = totals.melt(id_vars='source', var_name='type', value_name='count')

                fig_type = px.bar(
                    totals_melted,
                    x='source',
                    y='count',
                    color='type',
                    barmode='group',
                    title="Posts longs (>280 chars) vs courts"
                )
                st.plotly_chart(fig_type, use_container_width=True)

            st.subheader("Evolution de la longueur moyenne")
            fig_len_time = px.line(
                df_content,
                x='date',
                y='avg_length',
                color='source',
                color_discrete_map=SOURCE_COLORS,
                markers=True
            )
            st.plotly_chart(fig_len_time, use_container_width=True)

            st.dataframe(df_content, hide_index=True, use_container_width=True)
        else:
            st.info("Pas de stats contenu - Relancez le job d'agregation")

elif page == "Activite":
    st.title("Patterns d'Activite")
    st.caption("Analyse temporelle de l'activite")

    if not data['hourly'].empty:
        df_hourly = data['hourly'].copy()

        st.subheader("Activite par heure")

        sources = df_hourly['source'].unique().tolist()
        selected_sources = st.multiselect("Sources", sources, default=sources)

        df_filtered = df_hourly[df_hourly['source'].isin(selected_sources)]

        if not df_filtered.empty:
            hourly_agg = df_filtered.groupby('hour')['post_count'].sum().reset_index()

            fig_hourly = px.bar(
                hourly_agg,
                x='hour',
                y='post_count',
                title="Distribution par heure (UTC)",
                labels={'hour': 'Heure', 'post_count': 'Nombre de posts'}
            )
            fig_hourly.update_layout(xaxis=dict(tickmode='linear', dtick=1))
            st.plotly_chart(fig_hourly, use_container_width=True)

            st.subheader("Heatmap Source x Heure")

            pivot = df_filtered.pivot_table(
                index='source',
                columns='hour',
                values='post_count',
                aggfunc='sum',
                fill_value=0
            )

            fig_heatmap = px.imshow(
                pivot,
                labels=dict(x="Heure", y="Source", color="Posts"),
                color_continuous_scale='YlOrRd',
                aspect='auto'
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)

            if 'day_of_week' in df_filtered.columns:
                st.subheader("Activite par jour de la semaine")

                days_map = {1: 'Dim', 2: 'Lun', 3: 'Mar', 4: 'Mer', 5: 'Jeu', 6: 'Ven', 7: 'Sam'}
                df_filtered['day_name'] = df_filtered['day_of_week'].map(days_map)

                daily_agg = df_filtered.groupby('day_name')['post_count'].sum().reset_index()
                daily_agg['day_order'] = daily_agg['day_name'].map({v: k for k, v in days_map.items()})
                daily_agg = daily_agg.sort_values('day_order')

                fig_daily = px.bar(
                    daily_agg,
                    x='day_name',
                    y='post_count',
                    title="Distribution par jour",
                    labels={'day_name': 'Jour', 'post_count': 'Nombre de posts'}
                )
                st.plotly_chart(fig_daily, use_container_width=True)
    else:
        st.info("Pas de donnees d'activite horaire")

    st.markdown("---")
    st.subheader("Statistiques de Remapping")

    if not data['remapping'].empty:
        df_remap = data['remapping']

        col1, col2 = st.columns(2)

        with col1:
            fig_remap = px.bar(
                df_remap,
                x='source',
                y='remapped_pct',
                color='source',
                color_discrete_map=SOURCE_COLORS,
                title="Taux de remapping par source (%)"
            )
            fig_remap.update_layout(showlegend=False)
            st.plotly_chart(fig_remap, use_container_width=True)

        with col2:
            fig_kw_pct = px.bar(
                df_remap,
                x='source',
                y='keywords_pct',
                color='source',
                color_discrete_map=SOURCE_COLORS,
                title="Taux de posts avec keywords (%)"
            )
            fig_kw_pct.update_layout(showlegend=False)
            st.plotly_chart(fig_kw_pct, use_container_width=True)
    else:
        st.info("Pas de statistiques de remapping")

elif page == "Requetes SQL":
    st.title("Requetes SQL (Athena)")
    st.caption("Interrogez les donnees avec SQL via AWS Athena")

    ATHENA_DATABASE = "uccnt_dev_db"
    ATHENA_OUTPUT = f"s3://{CURATED_BUCKET}/athena-results/"

    @st.cache_resource
    def get_athena_client():
        return boto3.client('athena', region_name=AWS_REGION)

    def execute_athena_query(query, database=ATHENA_DATABASE):
        """Execute une requete Athena et retourne un DataFrame"""
        athena = get_athena_client()

        try:
            response = athena.start_query_execution(
                QueryString=query,
                QueryExecutionContext={'Database': database},
                ResultConfiguration={'OutputLocation': ATHENA_OUTPUT}
            )
            query_id = response['QueryExecutionId']

            while True:
                status = athena.get_query_execution(QueryExecutionId=query_id)
                state = status['QueryExecution']['Status']['State']

                if state == 'SUCCEEDED':
                    break
                elif state in ['FAILED', 'CANCELLED']:
                    error = status['QueryExecution']['Status'].get('StateChangeReason', 'Unknown error')
                    return None, f"Requete echouee: {error}"

                import time
                time.sleep(1)

            results = athena.get_query_results(QueryExecutionId=query_id)

            columns = [col['Label'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
            rows = results['ResultSet']['Rows'][1:]

            data = []
            for row in rows:
                data.append([cell.get('VarCharValue', '') for cell in row['Data']])

            return pd.DataFrame(data, columns=columns), None

        except Exception as e:
            return None, str(e)

    st.subheader("Exemples de requetes")

    example_queries = {
        "Volume par jour": """
SELECT date, source, total_posts
FROM volume_by_source
ORDER BY date DESC, total_posts DESC
LIMIT 50
""",
        "Volume par semaine": """
SELECT year_week, source, total_posts, unique_posts
FROM volume_by_week
ORDER BY year_week DESC
LIMIT 30
""",
        "Volume par mois": """
SELECT year_month, source, total_posts
FROM volume_by_month
ORDER BY year_month DESC
""",
        "Top 10 keywords": """
SELECT keyword, SUM(mentions) as total_mentions
FROM trending_keywords
GROUP BY keyword
ORDER BY total_mentions DESC
LIMIT 10
""",
        "Keywords viraux (multi-sources)": """
SELECT keyword, total_mentions, sources_count
FROM cross_source_keywords
WHERE sources_count >= 3
ORDER BY total_mentions DESC
LIMIT 20
""",
        "Taux de croissance": """
SELECT date, source, total_posts, growth_pct, growth_abs
FROM growth_rate
WHERE growth_pct IS NOT NULL
ORDER BY date DESC
LIMIT 50
""",
        "Stats contenu": """
SELECT date, source, avg_length, long_posts, short_posts
FROM content_stats
ORDER BY date DESC
LIMIT 30
""",
        "Activite par heure": """
SELECT hour, source, SUM(post_count) as total_posts
FROM hourly_activity
GROUP BY hour, source
ORDER BY hour, source
""",
        "Resume global": """
SELECT *
FROM global_summary
LIMIT 1
"""
    }

    selected_example = st.selectbox("Choisir un exemple", ["-- Selectionner --"] + list(example_queries.keys()))

    st.subheader("Votre requete")

    default_query = ""
    if selected_example != "-- Selectionner --":
        default_query = example_queries[selected_example].strip()

    query = st.text_area(
        "Requete SQL",
        value=default_query,
        height=150,
        placeholder="SELECT * FROM processed_data LIMIT 10"
    )

    col1, col2 = st.columns([1, 4])

    with col1:
        run_query = st.button("Executer", type="primary")

    with col2:
        st.caption(f"Base de donnees: {ATHENA_DATABASE}")

    if run_query and query.strip():
        with st.spinner("Execution de la requete..."):
            df_result, error = execute_athena_query(query)

            if error:
                st.error(f"Erreur: {error}")
            elif df_result is not None:
                st.success(f"Requete executee avec succes - {len(df_result)} lignes")

                st.dataframe(df_result, use_container_width=True, hide_index=True)

                csv = df_result.to_csv(index=False)
                st.download_button(
                    label="Telecharger CSV",
                    data=csv,
                    file_name="athena_results.csv",
                    mime="text/csv"
                )

    st.markdown("---")

    st.subheader("Tables disponibles")

    tables_info = """
| Table | Description | Colonnes principales |
|-------|-------------|---------------------|
| `volume_by_source` | Volume par jour | date, source, total_posts, unique_posts |
| `volume_by_week` | Volume par semaine | year_week, source, total_posts |
| `volume_by_month` | Volume par mois | year_month, source, total_posts |
| `growth_rate` | Croissance jour/jour | date, source, total_posts, growth_pct, growth_abs |
| `content_stats` | Stats contenu | date, source, avg_length, long_posts, short_posts |
| `trending_keywords` | Keywords tendance | date, keyword, mentions, sources_count |
| `cross_source_keywords` | Keywords multi-sources | keyword, total_mentions, sources_count, is_viral |
| `hourly_activity` | Activite par heure | source, hour, day_of_week, post_count |
| `global_summary` | Resume global | total_posts, active_sources, first_post, last_post |
| `source_summary` | Resume par source | source, total_posts, first_post, last_post |
"""
    st.markdown(tables_info)

    st.caption("Note: Les tables doivent etre creees dans le Glue Data Catalog via Terraform ou Athena CREATE EXTERNAL TABLE")

elif page == "Explorateur S3":
    st.title("Explorateur S3")
    st.caption("Navigation dans les donnees brutes")

    s3 = get_s3_client()

    bucket = st.selectbox("Bucket", [RAW_BUCKET, PROCESSED_BUCKET, CURATED_BUCKET])

    prefix = st.text_input("Prefix (dossier)", "")

    if st.button("Lister"):
        try:
            response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=100)
            objects = response.get('Contents', [])

            if objects:
                data_list = []
                for obj in objects:
                    data_list.append({
                        "Fichier": obj['Key'],
                        "Taille (KB)": round(obj['Size'] / 1024, 2),
                        "Modifie": obj['LastModified'].strftime('%Y-%m-%d %H:%M')
                    })

                st.dataframe(pd.DataFrame(data_list), hide_index=True, use_container_width=True)

                total_size = sum(obj['Size'] for obj in objects) / (1024 * 1024)
                st.caption(f"Total: {len(objects)} fichiers, {total_size:.2f} MB")
            else:
                st.warning("Aucun fichier trouve")
        except Exception as e:
            st.error(f"Erreur: {e}")

    st.markdown("---")

    st.subheader("Apercu fichier JSON")

    file_key = st.text_input("Chemin du fichier (ex: bluesky/year=2026/...)")

    if file_key and st.button("Charger l'apercu"):
        try:
            response = s3.get_object(Bucket=bucket, Key=file_key)
            content = response['Body'].read().decode('utf-8')

            lines = content.strip().split('\n')[:5]

            st.code('\n'.join(lines), language='json')
            st.caption(f"Affichage des 5 premieres lignes sur {len(content.strip().split(chr(10)))} total")
        except Exception as e:
            st.error(f"Erreur: {e}")

st.markdown("---")
st.caption(f"UCCNCT Dashboard | Donnees actualisees: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Sources: Bluesky, Nostr, HackerNews, StackOverflow, RSS")
