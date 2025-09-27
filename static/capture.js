(function () {
  // The width and height of the captured photo. We will set the
  // width to the value defined here, but the height will be
  // calculated based on the aspect ratio of the input stream.

  var width = 320;    // We will scale the photo width to this
  var height = 0;     // This will be computed based on the input stream

  // |streaming| indicates whether or not we're currently streaming
  // video from the camera. Obviously, we start at false.

  var streaming = false;

  // The various HTML elements we need to configure or control. These
  // will be set by the startup() function.

  var video = null;
  var canvas = null;
  // var photo = null;
  var startbutton = null;
  let socket = null;
  let mystream = null;

  function startup() {
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    // photo = document.getElementById('photo');
    capturebutton = document.getElementById('capture-button');
    clearbutton = document.getElementById('clear-btn');
    debugconsole = document.getElementById('debugconsole');

    // Получаем IP сервера автоматически или используем текущий хост
    const serverUrl = window.location.hostname + ':5000';
    socket = io(serverUrl, {
      maxHttpBufferSize: 1e8,
      // transports: ['websocket', 'polling']
    });

    navigator.mediaDevices.getUserMedia({
      audio: false,
      video: {
        width: { ideal: 2048 },
        height: { ideal: 2048 },
        facingMode: { exact: "environment" },
      }
    })
      .then(function (stream) {
        mystream = stream
        video.srcObject = stream;
        video.play();
      })
      .catch(function (err) {
        console.log("An error occurred: " + err);
      });

    video.addEventListener('canplay', function (ev) {
      if (!streaming) {
        height = video.videoHeight / (video.videoWidth / width);

        // Firefox currently has a bug where the height can't be read from
        // the video, so we will make assumptions if this happens.

        if (isNaN(height)) {
          height = width / (4 / 3);
        }

        // video.setAttribute('width', width);
        // video.setAttribute('height', height);
        // canvas.setAttribute('width', width);
        // canvas.setAttribute('height', height);
        streaming = true;
      }
    }, false);

    capturebutton.addEventListener('click', function () {
      takepicture();
    });

    clearbutton.addEventListener('click', function () {
      if (confirm('Вы уверены, что хотите закрыть эту коробку?')) {
        fetch('/clear_box', { method: 'POST' })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              //updateBarcodes();
            }
          });
      }
    });

    socket.on('update_barcodes', (data) => {
      updateBarcodes(data);
    });

    //clearphoto();
  }

  function finish() {
    // Очистка при закрытии
    if (mystream) {
      mystream.getTracks().forEach(track => track.stop());
    }
    if (socket) socket.disconnect();
  }

  // Fill the photo with an indication that none has been
  // captured.

  // function clearphoto() {
  //   var context = canvas.getContext('2d');
  //   context.fillStyle = "#AAA";
  //   context.fillRect(0, 0, canvas.width, canvas.height);

  //   var data = canvas.toDataURL('image/png');
  //   photo.setAttribute('src', data);
  // }

  // Capture a photo by fetching the current contents of the video
  // and drawing it into a canvas, then converting that to a PNG
  // format data URL. By drawing it on an offscreen canvas and then
  // drawing that to the screen, we can change its size and/or apply
  // other changes before drawing it.

  function takepicture() {
    if (width && height) {

      const track = mystream.getVideoTracks()[0];
      const settings = track.getSettings();


      canvas.width = settings.width;
      canvas.height = settings.height;
      var context = canvas.getContext('2d');
      context.drawImage(video, 0, 0, settings.width, settings.height);

      var imageData = canvas.toDataURL('image/jpeg');
      // debugconsole.innerHTML = Date.now()
      // Отправляем изображение на сервер
      socket.emit('frame_data', {
        image: imageData,
        timestamp: Date.now(),
        resolution: `${canvas.width}x${canvas.height}`
      });
      debugconsole.innerHTML = 'sent ' + settings.height + ' ' + settings.width + ' ' + Date.now()
      // photo.setAttribute('src', data);
    } else {
      // clearphoto();
    }
  }

  function updateBarcodes(data) {
    debugconsole.innerHTML = 'updateBarcodes: ' + Date.now()
    document.getElementById('box-number').textContent = data.box_number || 'Новая коробка';
    const container = document.getElementById('barcodes-container');
    container.innerHTML = '';
    data.barcodes.forEach(barcode => {
      const li = document.createElement('li');
      li.textContent = barcode;
      container.appendChild(li);
    });
    // Обновляем состояние кнопок
    document.getElementById('seal-btn').disabled = data.is_sealed;
  }

  // Set up our event listener to run the startup process
  // once loading is complete.
  window.addEventListener('load', startup, false);
  window.addEventListener('beforeunload', finish, false);
})();