def convert_keys_for_template(movies):
    """
    딕셔너리 키의 하이픈을 언더스코어로 변경하여 Django 템플릿에서 사용 가능하게 만듭니다.
    """
    converted_movies = []
    
    for movie in movies:
        converted_movie = {}
        for key, value in movie.items():
            # 하이픈을 언더스코어로 변경
            new_key = key.replace('-', '_')
            converted_movie[new_key] = value
        converted_movies.append(converted_movie)
    
    return converted_movies