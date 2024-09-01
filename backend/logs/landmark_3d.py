import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

# 주간 평균 이미지 생성 및 저장 함수
def create_landmark_image(landmarks):

    # 랜드마크 이름
    landmark_names = ['Left Shoulder', 'Right Shoulder', 'Left Ear', 'Right Ear', 'C7']

    # 랜드마크 좌표 추출
    x_coords = [landmarks['left_shoulder']['x'], landmarks['right_shoulder']['x'],
                landmarks['left_ear']['x'], landmarks['right_ear']['x'],
                landmarks['c7']['x']]
    y_coords = [-landmarks['left_shoulder']['y'], -landmarks['right_shoulder']['y'],
                -landmarks['left_ear']['y'], -landmarks['right_ear']['y'],
                -landmarks['c7']['y']]
    z_coords = [landmarks['left_shoulder']['z'], landmarks['right_shoulder']['z'],
                landmarks['left_ear']['z'], landmarks['right_ear']['z'],
                landmarks['c7']['z']]

    # C7의 좌표 (리스트의 마지막 요소)
    c7_x, c7_y, c7_z = x_coords[-1], y_coords[-1], z_coords[-1]

    # # X축의 범위를 좁히기 위해 현재 X 좌표들의 범위를 확인
    y_min, y_max = min(y_coords), max(y_coords)
    y_range = y_max - y_min

    # 시각화 설정
    fig = plt.figure(figsize=(6, 7))
    ax = fig.add_subplot(111, projection='3d')  # 3D 축 추가
    ax.set_facecolor('#8871e6')  # 배경색 설정

    # C7을 기준으로 모든 포인트 연결
    for i in range(len(x_coords) - 1):  # C7은 마지막 요소이므로 제외
        ax.plot([c7_x, x_coords[i]], [c7_y, y_coords[i]], [c7_z, z_coords[i]], color='#ddddf5', linewidth=2)

    # 각 랜드마크를 점으로 표시
    ax.scatter(x_coords, y_coords, z_coords, color='yellow')

    # 각 랜드마크의 이름을 그래프에 표시
    for i, name in enumerate(landmark_names):
        ax.text(x_coords[i], y_coords[i], z_coords[i], name, fontsize=10, color='white', ha='center', va='bottom',
            bbox=dict(facecolor='black', alpha=0.5, edgecolor='none', pad=1.5)
        )

    # Y축의 범위를 조정 (예: 범위를 60% 정도로 확대/축소)
    adjust_factor = 0.6  # 이 값을 조절해서 범위를 더 좁히거나 넓힐 수 있음
    ax.set_ylim([y_min - y_range * adjust_factor, y_max + y_range * adjust_factor])

    # y축 반전 및 눈금 제거
    ax.invert_zaxis()  # Z축을 반전하여 사람이 서있는 것처럼 보이게 함

    # 시점 설정 (필요에 따라 조정)
    ax.view_init(elev=32, azim=-34)  # 시점 조정 (elev: 높이, azim: 좌우 회전)

    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False) #눈금 없애기

    # 바깥 border 선 없애기
    for spine in ax.spines.values():
        spine.set_visible(False)
    
    # 이미지를 임시 메모리 버퍼에 저장하고 base64 인코딩
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0.1)
    buffer.seek(0)
    img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close()

    return img_str