// static/js/main.js

import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
// VRM用のライブラリを一つのimport文にまとめる
import { VRMLoaderPlugin } from '@pixiv/three-vrm';
import { VRMAnimationLoaderPlugin } from "https://cdn.jsdelivr.net/npm/@pixiv/three-vrm-animation/lib/three-vrm-animation.module.js";

// --- 認証関連の状態管理 ---
let isLoggedIn = false;
let accessToken = null;
let userModels = [];
let currentModelId = null;

// --- 背景画像の状態管理 ---
let userBackgrounds = [];
let currentBackgroundId = null;

// --- キャラクターの状態を示す定数 ---
const CHARACTER_STATES = {
    IDLE: 'idle',
    WALKING: 'walking',
    ACTION: 'action'
};

// --- キャラクターの現在の状態 ---
let characterState = CHARACTER_STATES.IDLE;
let walkDestination = new THREE.Vector3();
let nextStateChangeTime = 0;

// --- Scene, Camera, Renderer Setup ---
const scene = new THREE.Scene();
scene.background = null; //cssで背景を適応できるようにnullに
const camera = new THREE.PerspectiveCamera(45, 1024 / 600, 0.1, 1000);
camera.position.set(0, 1.5, 2.2); // キャラクターが見やすいようにカメラ位置を調整
const renderer = new THREE.WebGLRenderer({
    antialias: false, // パフォーマンス向上のためfalse
    alpha: true
});
renderer.setPixelRatio(window.devicePixelRatio); // パフォーマンス向上のため解像度を下げる
renderer.shadowMap.enabled = true; // パフォーマンス向上のため影を無効化
const container = document.getElementById('canvas-container');
if (container) {
    renderer.setSize(1024, 600); // 画面サイズを1024x600に設定
    container.appendChild(renderer.domElement);
}

// --- 改良されたライティングセットアップ ---
const ambientLight = new THREE.AmbientLight(0xffffff, 1.2);
scene.add(ambientLight);

const directionalLight = new THREE.DirectionalLight(0xffffff, 1.2);
directionalLight.position.set(0, 10, 10);
directionalLight.castShadow = true;
scene.add(directionalLight);

const frontLight = new THREE.DirectionalLight(0xffffff, 0.8);
frontLight.position.set(0, 1.5, 5);
scene.add(frontLight);

const rightLight = new THREE.DirectionalLight(0xffffee, 0.5);
rightLight.position.set(5, 2, 0);
scene.add(rightLight);

const leftLight = new THREE.DirectionalLight(0xeeffff, 0.5);
leftLight.position.set(-5, 2, 0);
scene.add(leftLight);

// --- Animation Variables ---
const clock = new THREE.Clock();
let mixer;
let currentVrm = null;
let currentVrmAction = null;
let walkingAnimation = null;
let idleAnimation = null;
let actionAnimations = [];

// --- GLTFLoaderにVRMプラグインを登録 ---
const loader = new GLTFLoader();
loader.register((parser) => {
    return new VRMLoaderPlugin(parser, { autoUpdateHumanBones: true });
});

// --- API操作のための関数群 ---
// ログイン処理
async function login(email, password) {
    try {
        const formData = new FormData();
        formData.append('username', email); // FastAPIのOAuth2はusernameパラメータを使用
        formData.append('password', password);

        const response = await fetch('/token', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'ログインに失敗しました');
        }

        const data = await response.json();
        accessToken = data.access_token;
        
        // トークンをlocalStorageに保存
        localStorage.setItem('accessToken', accessToken);
        
        return true;
    } catch (error) {
        console.error('Login error:', error);
        return false;
    }
}

// ユーザー登録処理
async function register(email, password) {
    try {
        const response = await fetch('/users/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email,
                password
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '登録に失敗しました');
        }

        // 登録成功後、自動ログイン
        return await login(email, password);
    } catch (error) {
        console.error('Registration error:', error);
        return false;
    }
}

// モデル一覧取得
async function fetchModels() {
    try {
        const response = await fetch('/models/', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Models fetch failed:', {
                status: response.status,
                statusText: response.statusText,
                body: errorText
            });
            throw new Error(`モデル一覧の取得に失敗しました (${response.status}): ${errorText}`);
        }

        userModels = await response.json();
        return userModels;
    } catch (error) {
        console.error('Error fetching models:', error);
        return [];
    }
}

// モデルアップロード
async function uploadModel(formData) {
    try {
        const response = await fetch('/upload/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            },
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Model upload failed:', {
                status: response.status,
                statusText: response.statusText,
                body: errorText
            });
            throw new Error(`モデルのアップロードに失敗しました (${response.status}): ${errorText}`);
        }

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Upload error:', error);
        return null;
    }
}

// 背景画像をアップロードする関数
async function uploadBackground(formData) {
    try {
        const response = await fetch('/upload-background/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            },
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Background upload failed:', {
                status: response.status,
                statusText: response.statusText,
                body: errorText
            });
            throw new Error(`背景画像のアップロードに失敗しました (${response.status}): ${errorText}`);
        }

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Background upload error:', error);
        return null;
    }
}

// ユーザーの背景画像一覧を取得する関数
async function fetchBackgrounds() {
    try {
        const response = await fetch('/backgrounds/', {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Backgrounds fetch failed:', {
                status: response.status,
                statusText: response.statusText,
                body: errorText
            });
            throw new Error(`背景画像一覧の取得に失敗しました (${response.status}): ${errorText}`);
        }

        userBackgrounds = await response.json();
        return userBackgrounds;
    } catch (error) {
        console.error('Error fetching backgrounds:', error);
        return [];
    }
}

// 背景画像を設定する関数
function setBackground(backgroundPath) {
    const canvasContainer = document.getElementById('canvas-container');
    if (canvasContainer) {
        canvasContainer.style.backgroundImage = `url('${backgroundPath}')`;
    }
}

// --- UI操作のための関数群 ---
// ログイン/登録フォーム切り替え
function toggleAuthForm(isLogin) {
    const formTitle = document.querySelector('#login-form h2');
    const submitButton = document.getElementById('login-button');
    const toggleButton = document.getElementById('register-toggle');
    
    if (isLogin) {
        formTitle.textContent = 'ログイン';
        submitButton.textContent = 'ログイン';
        toggleButton.textContent = '新規登録';
    } else {
        formTitle.textContent = '新規登録';
        submitButton.textContent = '登録';
        toggleButton.textContent = 'ログイン画面に戻る';
    }
}

// 認証フォーム送信処理
async function handleAuthSubmit(e, isLogin) {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const messageEl = document.getElementById('auth-message');
    
    let success = false;
    
    if (isLogin) {
        success = await login(email, password);
    } else {
        success = await register(email, password);
    }
    
    if (success) {
        // ログインが成功したらUIを切り替え
        document.getElementById('login-container').style.display = 'none';
        document.getElementById('app-container').style.display = 'block';
        
        // モデルを読み込む
        await loadUserModels();
    } else {
        messageEl.textContent = isLogin ? 
            'ログインに失敗しました。メールアドレスとパスワードを確認してください。' : 
            '登録に失敗しました。別のメールアドレスを使用するか、管理者に連絡してください。';
    }
}

// ログアウト処理
function logout() {
    localStorage.removeItem('accessToken');
    accessToken = null;
    isLoggedIn = false;
    userModels = [];
    
    // UIをリセット
    if (currentVrm) {
        scene.remove(currentVrm.scene);
        currentVrm = null;
    }
    
    document.getElementById('app-container').style.display = 'none';
    document.getElementById('login-container').style.display = 'flex';
}

// 設定パネルの表示制御
function toggleSettingsPanel() {
    const panel = document.getElementById('settings-panel');
    const overlay = document.getElementById('overlay');
    
    panel.classList.toggle('active');
    overlay.classList.toggle('active');
}

// キャラクターリストUIの生成
function createCharacterList(models) {
    const listEl = document.getElementById('character-list');
    listEl.innerHTML = '';
    
    if (models.length === 0) {
        listEl.innerHTML = '<p>利用可能なモデルがありません。モデルをアップロードしてください。</p>';
        return;
    }
    
    models.forEach(model => {
        const button = document.createElement('button');
        button.textContent = model.name;
        button.onclick = () => loadModel(model.id);
        listEl.appendChild(button);
    });
}

// ユーザーの背景画像を読み込む
async function loadUserBackgrounds() {
    if (!accessToken) {
        console.log('Not logged in, setting default background');
        setBackground('/static/uploads/backgrounds/default.jpg');
        currentBackgroundId = 'default';
        createBackgroundLibrary([]); // 空の配列でライブラリを作成
        return;
    }
    
    try {
        const backgrounds = await fetchBackgrounds();
        createBackgroundLibrary(backgrounds);
        
        // 背景画像がある場合は最初の画像を設定、なければデフォルト画像
        if (backgrounds && backgrounds.length > 0) {
            setBackground(backgrounds[0].path);
            currentBackgroundId = backgrounds[0].id;
        } else {
            setBackground('/static/uploads/backgrounds/default.jpg');
            currentBackgroundId = 'default';
        }
    } catch (error) {
        console.error("背景画像の読み込みに失敗しました:", error);
        // エラー時はデフォルト背景を使用
        setBackground('/static/uploads/backgrounds/default.jpg');
        currentBackgroundId = 'default';
        createBackgroundLibrary([]); // 空の配列でライブラリを作成
    }
}

// 背景画像ライブラリUIの生成
function createBackgroundLibrary(backgrounds) {
    const libraryEl = document.getElementById('background-library');
    libraryEl.innerHTML = '';
    
    // デフォルト背景画像を追加
    const defaultThumbnail = document.createElement('div');
    defaultThumbnail.className = 'bg-thumbnail';
    defaultThumbnail.style.backgroundImage = "url('/static/uploads/backgrounds/default.jpg')";
    defaultThumbnail.dataset.path = '/static/uploads/backgrounds/default.jpg';
    defaultThumbnail.dataset.id = 'default';
    
    // デフォルトが選択中なら active クラスを追加
    if (currentBackgroundId === 'default' || !currentBackgroundId) {
        defaultThumbnail.classList.add('active');
    }
    
    defaultThumbnail.addEventListener('click', () => {
        document.querySelectorAll('.bg-thumbnail').forEach(el => el.classList.remove('active'));
        defaultThumbnail.classList.add('active');
        setBackground('/static/uploads/backgrounds/default.jpg');
        currentBackgroundId = 'default';
    });
    
    libraryEl.appendChild(defaultThumbnail);
    
    // ユーザーアップロード画像を追加
    if (backgrounds && backgrounds.length > 0) {
        backgrounds.forEach(bg => {
            const thumbnail = document.createElement('div');
            thumbnail.className = 'bg-thumbnail';
            thumbnail.style.backgroundImage = `url('${bg.path}')`;
            thumbnail.dataset.id = bg.id;
            thumbnail.dataset.path = bg.path;
            
            // 現在選択中の背景にはactiveクラスを追加
            if (bg.id === currentBackgroundId) {
                thumbnail.classList.add('active');
            }
            
            thumbnail.addEventListener('click', () => {
                // 全てのサムネイルからactiveクラスを削除
                document.querySelectorAll('.bg-thumbnail').forEach(el => el.classList.remove('active'));
                // クリックされたサムネイルにactiveクラスを追加
                thumbnail.classList.add('active');
                // 背景を変更
                setBackground(bg.path);
                currentBackgroundId = bg.id;
            });
            
            libraryEl.appendChild(thumbnail);
        });
    } else if (!backgrounds) {
        // backgrounds が undefined または null の場合
        libraryEl.innerHTML += '<p>背景画像の取得に失敗しました。</p>';
    } else {
        // 背景画像が0件の場合
        libraryEl.innerHTML += '<p>利用可能な背景画像がありません。画像をアップロードしてください。</p>';
    }
}

// --- モデルと背景画像の読み込み ---
// ユーザーのモデルを読み込む
async function loadUserModels() {
    if (!accessToken) {
        console.log('Not logged in, skipping model loading');
        return;
    }
    
    const models = await fetchModels();
    createCharacterList(models);
    
    // モデルがある場合は最初のモデルを読み込む
    if (models.length > 0) {
        await loadModel(models[0].id);
    }
}

// 特定のモデルを読み込む
async function loadModel(modelId) {
    currentModelId = modelId;
    const model = userModels.find(m => m.id === modelId);
    
    if (!model) return;
    
    await loadVrmFromPath(model.vrm_path);
    
    // アニメーションも読み込む
    actionAnimations = [];
    
    for (const anim of model.animations) {
        if (anim.anim_name.toLowerCase().includes('walk')) {
            await loadWalkAnimation(anim.vrma_path);
        } else if (anim.anim_name.toLowerCase().includes('idle')) {
            await loadIdleAnimation(anim.vrma_path);
        } else {
            const animation = await loadActionAnimation(anim.vrma_path);
            if (animation) {
                actionAnimations.push(animation);
            }
        }
    }
    
    // デフォルトでIDLE状態にする
    characterState = CHARACTER_STATES.IDLE;
    
    // 設定パネルを閉じる
    toggleSettingsPanel();
}

// --- VRMとアニメーション読み込み関連の関数群 ---
// VRMモデルを読み込む
async function loadVrmFromPath(path) {
    try {
        // 以前のモデルがある場合は削除
        if (currentVrm) {
            scene.remove(currentVrm.scene);
            if (currentVrmAction) {
                currentVrmAction.stop();
            }
            mixer = null;
            currentVrm = null;
            currentVrmAction = null;
        }

        console.log(`Loading VRM model: ${path}...`);
        const gltf = await loader.loadAsync(path);
        currentVrm = gltf.userData.vrm;

        // キャラクターの向きと位置を調整
        currentVrm.scene.rotation.y = Math.PI;
        
        // キャラクターの位置を画面中央に調整
        currentVrm.scene.position.y = 0.5;
        
        scene.add(currentVrm.scene);
        console.log('VRM model loaded successfully.');
        
        // ミキサーを準備
        mixer = new THREE.AnimationMixer(currentVrm.scene);
        
        return true;
    } catch (error) {
        console.error('Error loading VRM model:', error);
        showErrorMessage('モデルの読み込み中にエラーが発生しました。');
        return false;
    }
}

// 歩行アニメーションを読み込む
async function loadWalkAnimation(path) {
    try {
        const animation = await loadVrmAnimation(path);
        if (animation) {
            walkingAnimation = animation;
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error loading walk animation:', error);
        return false;
    }
}

// アイドルアニメーションを読み込む
async function loadIdleAnimation(path) {
    try {
        const animation = await loadVrmAnimation(path);
        if (animation) {
            idleAnimation = animation;
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error loading idle animation:', error);
        return false;
    }
}

// アクションアニメーションを読み込む
async function loadActionAnimation(path) {
    try {
        return await loadVrmAnimation(path);
    } catch (error) {
        console.error('Error loading action animation:', error);
        return null;
    }
}

// VRMアニメーションを読み込む
async function loadVrmAnimation(path) {
    try {
        console.log(`Loading VRMA animation: ${path}...`);

        // アニメーション用のローダーを準備
        const vrmaLoader = new GLTFLoader();
        vrmaLoader.register((parser) => {
            return new VRMAnimationLoaderPlugin(parser);
        });

        // アニメーションを読み込む
        const vrmaGltf = await vrmaLoader.loadAsync(path);
        console.log('VRMA animation loaded successfully.');

        // アニメーションを取得して返す
        if (vrmaGltf.userData.vrmAnimations && vrmaGltf.userData.vrmAnimations.length > 0) {
            return vrmaGltf.userData.vrmAnimations[0];
        }
        
        return null;
    } catch (error) {
        console.error('Error loading animation:', error);
        return null;
    }
}

// アニメーションを再生する
function playAnimation(animation) {
    if (!currentVrm || !animation || !mixer) return false;
    
    try {
        // 現在のアニメーションを停止
        if (currentVrmAction) {
            currentVrmAction.stop();
        }
        
        // humanoidTracksがある場合、それを使用してAnimationClipを作成
        if (animation.humanoidTracks && Object.keys(animation.humanoidTracks).length > 0) {
            const tracks = [];
            
            // 全てのhumanoidTracksから適切なKeyframeTracksを作成
            for (const boneName of Object.keys(animation.humanoidTracks)) {
                const boneTrack = animation.humanoidTracks[boneName];
                if (!boneTrack) continue;
                
                // ヒューマノイドボーンのマッピング
                const vrmBoneName = currentVrm.humanoid?.getBoneNode(boneName)?.name;
                if (!vrmBoneName) continue;
                
                // トラックパスを生成
                const trackPath = `${vrmBoneName}.quaternion`;
                
                // キーフレームトラックを作成 (回転情報)
                if (boneTrack.rotations && boneTrack.rotations.times.length > 0) {
                    const rotationTrack = new THREE.QuaternionKeyframeTrack(
                        trackPath,
                        boneTrack.rotations.times,
                        boneTrack.rotations.values
                    );
                    tracks.push(rotationTrack);
                }
                
                // 位置情報があれば追加
                if (boneTrack.translations && boneTrack.translations.times.length > 0) {
                    const translationPath = `${vrmBoneName}.position`;
                    const translationTrack = new THREE.VectorKeyframeTrack(
                        translationPath,
                        boneTrack.translations.times,
                        boneTrack.translations.values
                    );
                    tracks.push(translationTrack);
                }
            }
            
            if (tracks.length > 0) {
                const clip = new THREE.AnimationClip('vrmAnimation', animation.duration, tracks);
                
                // ミキサーでアニメーションを再生
                currentVrmAction = mixer.clipAction(clip);
                currentVrmAction.setLoop(THREE.LoopRepeat);
                currentVrmAction.play();
                return true;
            }
        }
        
        // フォールバックとして、フェイクアニメーションを適用
        return createFallbackAnimation();
    } catch (error) {
        console.error('Error playing animation:', error);
        return createFallbackAnimation();
    }
}

// フォールバックアニメーション（モデルが動かない場合の対応）
function createFallbackAnimation() {
    try {
        if (!currentVrm || !mixer) return false;
        
        console.log('Creating fallback animation');
        
        // 頭部のわずかな回転アニメーション
        const headNode = currentVrm.humanoid?.getBoneNode('head');
        const tracks = [];
        
        if (headNode) {
            const times = [0, 1, 2, 3, 4];
            const headRotValues = [
                0, 0, 0, 1,                  // 0秒: 初期位置
                0.05, 0.1, 0, 0.99,          // 1秒: 少し右上を向く
                0, 0.05, 0, 0.998,           // 2秒: 右を向く
                -0.05, -0.05, 0, 0.997,      // 3秒: 左下を向く
                0, 0, 0, 1                   // 4秒: 初期位置に戻る
            ];
            
            const headRotTrack = new THREE.QuaternionKeyframeTrack(
                `${headNode.name}.quaternion`,
                times,
                headRotValues
            );
            tracks.push(headRotTrack);
        }
        
        if (tracks.length > 0) {
            const clip = new THREE.AnimationClip('fallbackAnimation', 4, tracks);
            currentVrmAction = mixer.clipAction(clip);
            currentVrmAction.setLoop(THREE.LoopRepeat);
            currentVrmAction.play();
            return true;
        }
        
        return false;
    } catch (error) {
        console.error('Error creating fallback animation:', error);
        return false;
    }
}

// エラーメッセージ表示
function showErrorMessage(message) {
    if (container) {
        const errorText = document.createElement('p');
        errorText.textContent = message;
        errorText.style.cssText = `
            color: red;
            text-align: center;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 255, 255, 0.8);
            padding: 10px;
            border-radius: 5px;
            z-index: 5;
        `;
        container.appendChild(errorText);
        
        // 数秒後にエラーメッセージを消す
        setTimeout(() => {
            errorText.remove();
        }, 5000);
    }
}

// --- キャラクターの行動を更新する関数 ---
function updateCharacterBehavior(delta) {
    // 現在の時間を取得
    const now = Date.now() / 1000; // 秒単位の時間
    
    // 状態変更のタイミングをチェック
    if (now > nextStateChangeTime) {
        // ランダムな間隔（5〜15秒）で状態を変更
        nextStateChangeTime = now + 5 + Math.random() * 10;
        
        // ランダムに次の状態を決定
        const states = Object.values(CHARACTER_STATES);
        const nextState = states[Math.floor(Math.random() * states.length)];
        
        // 状態を変更
        characterState = nextState;
        
        if (characterState === CHARACTER_STATES.WALKING) {
            // 移動先をランダムに設定
            walkDestination = new THREE.Vector3(
                (Math.random() * 2 - 1) * 2, // X: -2〜2の範囲
                0,                           // Y: 高さは変更なし
                (Math.random() * 2 - 1) * 2  // Z: -2〜2の範囲
            );
        }    }
    
    // 現在の状態に応じた処理
    switch (characterState) {
        case CHARACTER_STATES.IDLE:
            // アイドル状態ではデフォルトのアニメーションを再生
            try {
                playAnimationByType('idle');
            } catch (error) {
                console.log('Idle animation playback error:', error);
            }
            break;
            
        case CHARACTER_STATES.WALKING:
            // 歩行状態では歩行アニメーションを再生
            try {
                playAnimationByType('walking');
            } catch (error) {
                console.log('Walking animation playback error:', error);
            }
            
            // 歩行目的地に向けて少しずつ移動
            if (currentVrm) {
                // 現在位置と目的地との距離を計算
                const currentPos = new THREE.Vector3().copy(currentVrm.scene.position);
                const direction = new THREE.Vector3().subVectors(walkDestination, currentPos);
                const distance = direction.length();
                
                // 一定距離以上離れている場合は移動
                if (distance > 0.1) {
                    direction.normalize();
                    // 移動速度
                    const speed = 0.5 * delta;
                    // 移動量を計算
                    const moveAmount = Math.min(speed, distance);
                    // 移動方向に進む
                    currentVrm.scene.position.add(direction.multiplyScalar(moveAmount));
                    
                    // モデルを移動方向に向ける
                    if (direction.x !== 0 || direction.z !== 0) {
                        const angle = Math.atan2(direction.x, direction.z);
                        currentVrm.scene.rotation.y = angle;
                    }
                }
            }
            break;        case CHARACTER_STATES.ACTION:
            // アクション状態ではランダムなアクションアニメーションを再生
            try {
                playAnimationByType('action');
            } catch (error) {
                console.log('Action animation playback error:', error);
            }
            break;
    }
}

// 指定した種類のアニメーションを再生する関数
function playAnimationByType(type) {
    // アニメーションが初期化されていない場合は何もしない
    if (!mixer) return;
    
    let targetAnimation = null;
    
    switch (type) {
        case 'idle':
            targetAnimation = idleAnimation;
            break;
        case 'walking':
            targetAnimation = walkingAnimation;
            break;
        case 'action':
            // アクションアニメーションがある場合はランダムに選択
            if (actionAnimations.length > 0) {
                targetAnimation = actionAnimations[Math.floor(Math.random() * actionAnimations.length)];
            } else {
                targetAnimation = idleAnimation; // アクションがなければアイドル
            }
            break;
    }
    
    // すでに同じアニメーションを再生中なら何もしない
    if (currentVrmAction === targetAnimation || !targetAnimation) return;
    
    // 前のアニメーションをフェードアウト
    if (currentVrmAction) {
        currentVrmAction.fadeOut(0.5);
    }
      // 新しいアニメーションをフェードイン
    currentVrmAction = targetAnimation;
    currentVrmAction.reset();
    currentVrmAction.fadeIn(0.5);
    currentVrmAction.play();
}

// --- 改良されたレンダーループ ---
function animate() {
    requestAnimationFrame(animate);
    const delta = clock.getDelta();

    // アニメーションミキサーを更新
    if (mixer) {
        mixer.update(delta);
    }

    // VRMの更新
    if (currentVrm) {
        // VRMモデルの更新
        currentVrm.update(delta);

        // キャラクターの行動を更新
        updateCharacterBehavior(delta);

        // 小さな自然なゆらぎを追加
        const time = clock.getElapsedTime();
        const breathingMotion = Math.sin(time * 0.5) * 0.005;
        currentVrm.scene.position.y = 0.5 + breathingMotion; // 基本位置に呼吸動作を加算
    }

    // シーンをレンダリング
    renderer.render(scene, camera);
}

// --- 初期化とイベントリスナーの設定 ---
function init() {
    // ローカルストレージからトークンを取得
    accessToken = localStorage.getItem('accessToken');
    
    // トークンがある場合はログイン済みとして扱う
    if (accessToken) {
        isLoggedIn = true;
        document.getElementById('login-container').style.display = 'none';
        document.getElementById('app-container').style.display = 'block';
        
        // モデル一覧を取得
        loadUserModels();
        
        // 背景画像一覧を取得
        loadUserBackgrounds();
    }
    
    // ハンバーガーメニューのクリックイベント
    document.getElementById('menu-icon').addEventListener('click', toggleSettingsPanel);
    
    // オーバーレイのクリックイベント（設定パネルを閉じる）
    document.getElementById('overlay').addEventListener('click', toggleSettingsPanel);
    
    // 閉じるボタンのクリックイベント
    document.getElementById('close-panel')?.addEventListener('click', toggleSettingsPanel);
    
    // ログアウトボタンのクリックイベント
    document.getElementById('logout-button')?.addEventListener('click', logout);
    
    // 認証フォームのイベント
    const authForm = document.getElementById('auth-form');
    if (authForm) {
        let isLoginMode = true;
        
        // フォーム送信イベント
        authForm.addEventListener('submit', (e) => handleAuthSubmit(e, isLoginMode));
        
        // 切り替えボタンのクリックイベント
        document.getElementById('register-toggle').addEventListener('click', () => {
            isLoginMode = !isLoginMode;
            toggleAuthForm(isLoginMode);
        });
    }
    
    // アップロードフォームのイベント
    const uploadForm = document.getElementById('upload-form');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(uploadForm);
            const messageEl = document.getElementById('upload-message');
            
            messageEl.textContent = 'アップロード中...';
            
            const result = await uploadModel(formData);
            
            if (result) {
                messageEl.textContent = 'モデルが正常にアップロードされました。';
                uploadForm.reset();
                
                // モデル一覧を再取得
                await loadUserModels();
            } else {
                messageEl.textContent = 'アップロードに失敗しました。もう一度お試しください。';
            }
        });
    }
    
    // 背景画像アップロードフォームのイベント
    const backgroundUploadForm = document.getElementById('background-upload-form');
    if (backgroundUploadForm) {
        backgroundUploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(backgroundUploadForm);
            const messageEl = document.getElementById('background-upload-message');
            
            messageEl.textContent = 'アップロード中...';
            messageEl.className = '';
            
            try {
                // フォームデータのキー名がHTML内のinput要素と一致していることを確認
                const fileInput = document.getElementById('background-file');
                if (fileInput && fileInput.files[0]) {
                    // すでに追加されている場合は一度削除して再追加
                    if (formData.has('background_file')) {
                        formData.delete('background_file');
                    }
                    formData.append('background_file', fileInput.files[0]);
                }
                
                const result = await uploadBackground(formData);
                
                if (result) {
                    messageEl.textContent = '背景画像が正常にアップロードされました。';
                    messageEl.className = '';
                    backgroundUploadForm.reset();
                    
                    // 背景画像一覧を再取得
                    await loadUserBackgrounds();
                    
                    // アップロードした背景をすぐに設定
                    if (result.path) {
                        setBackground(result.path);
                        currentBackgroundId = result.id;
                        
                        // 全てのサムネイルからactiveクラスを削除
                        document.querySelectorAll('.bg-thumbnail').forEach(el => {
                            if (el.dataset.id === result.id) {
                                el.classList.add('active');
                            } else {
                                el.classList.remove('active');
                            }
                        });
                    }
                } else {
                    messageEl.textContent = 'アップロードに失敗しました。もう一度お試しください。';
                    messageEl.className = 'error';
                }
            } catch (error) {
                console.error('Background upload error:', error);
                messageEl.textContent = `アップロードエラー: ${error.message || '不明なエラー'}`;
                messageEl.className = 'error';
            }
        });
    }
    
    // アニメーションループを開始
    animate();
}

// 初期化を実行
init();
