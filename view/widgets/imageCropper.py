import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from ttkbootstrap import Style
from PIL import Image, ImageTk


class ImageCropper(tk.Toplevel):
    # 固定視窗大小
    WINDOW_WIDTH = 1344
    WINDOW_HEIGHT = 756

    # 按鈕區域高度
    PANEL_HEIGHT = 52

    # 最大縮放比例
    MAX_SCALE = 10.0

    # 每次縮放增減比例
    SCALE_STEP = 0.2

    # 控制點大小
    HANDLE_SIZE = 8

    def __init__(self, master, imagePath):
        super().__init__(master)

        # 初始化基本設定
        self._initializeWindow()
        self._loadImage(imagePath)
        self._setupCanvas()
        self._calculateImageSize()
        self._initializeImageDisplay()
        self._initializeState()
        self._bindEvents()
        self._createButtonPanel()

    def _initializeWindow(self):
        """初始化視窗設定"""
        Style(theme="minty")

        self.title("圖片裁切器")
        self.resizable(False, False)

        # 設定固定視窗大小
        screenWidth = self.winfo_screenwidth()
        screenHeight = self.winfo_screenheight()

        positionX = max(0, (screenWidth - self.WINDOW_WIDTH) // 2)
        positionY = max(
            0, (screenHeight - (self.WINDOW_HEIGHT + self.PANEL_HEIGHT)) // 2
        )

        self.geometry(
            f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}+{positionX}+{positionY}"
        )

    def _loadImage(self, imagePath):
        """載入圖片"""
        self.originalImage = Image.open(imagePath)
        self.scale = 1.0

    def _setupCanvas(self):
        """設定 Canvas"""
        canvasHeight = self.WINDOW_HEIGHT - self.PANEL_HEIGHT
        self.canvas = tk.Canvas(
            self, width=self.WINDOW_WIDTH, height=canvasHeight, cursor="cross"
        )
        self.canvas.pack()

    def _calculateImageSize(self):
        """計算圖片大小並調整縮放比例"""

        # 初始圖片大小 (依縮放比例)
        width, height = self.originalImage.size
        self.imageWidth = int(width * self.scale)
        self.imageHeight = int(height * self.scale)

        # 限制圖片大小不超過 Canvas
        maxWidth = self.WINDOW_WIDTH
        maxHeight = self.WINDOW_HEIGHT - self.PANEL_HEIGHT

        if self.imageWidth > maxWidth or self.imageHeight > maxHeight:
            ratioWidth = maxWidth / self.imageWidth
            ratioHeight = maxHeight / self.imageHeight
            limitScale = min(ratioWidth, ratioHeight)
            self.scale *= limitScale
            self.imageWidth = int(width * self.scale)
            self.imageHeight = int(height * self.scale)

    def _initializeImageDisplay(self):
        """初始化圖片顯示"""

        # 圖片顯示的偏移量 (圖片左上角在 Canvas 的座標)
        self.offsetX = 0
        self.offsetY = 0

        self._updateImage()

        self.imageId = self.canvas.create_image(
            self.offsetX, self.offsetY, anchor="nw", image=self.photo
        )

    def _initializeState(self):
        """初始化狀態變數"""

        # 選取矩形相關
        self.rectangleCoordinates = None
        self.rectangleId = None
        self.handles = {}

        # 拖曳矩形相關
        self.isDragging = False
        self.dragHandle = None
        self.startX = None
        self.startY = None

        # 拖曳圖片相關
        self.isDraggingImage = False
        self.dragImageStart = None
        self.startOffsetX = 0
        self.startOffsetY = 0

    def _bindEvents(self):
        """綁定所有事件"""

        # 左鍵事件
        self.canvas.bind("<ButtonPress-1>", self.onMouseDown)
        self.canvas.bind("<B1-Motion>", self.onMouseMove)
        self.canvas.bind("<ButtonRelease-1>", self.onMouseUp)
        self.canvas.bind("<Double-Button-1>", self.onDoubleClick)

        # 右鍵事件
        self.canvas.bind("<ButtonPress-3>", self.onRightMouseDown)
        self.canvas.bind("<B3-Motion>", self.onRightMouseMove)
        self.canvas.bind("<ButtonRelease-3>", self.onRightMouseUp)

        # 滾輪事件
        self.canvas.bind("<MouseWheel>", self.onMouseWheel)

    def _updateImage(self):
        """依照目前比例重新產生圖片"""
        width, height = self.originalImage.size
        newWidth = int(width * self.scale)
        newHeight = int(height * self.scale)
        self.imageWidth = newWidth
        self.imageHeight = newHeight

        self.image = self.originalImage.resize((newWidth, newHeight), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(self.image)

    def _createButtonPanel(self):
        """建立按鈕和座標顯示區域"""
        bottomFrame = tk.Frame(self)
        bottomFrame.pack(expand=True, fill="x", padx=12, pady=0)

        # 左側座標顯示
        coordinateFrame = tk.Frame(bottomFrame)
        coordinateFrame.pack(side="left", fill="x", expand=True)

        tk.Label(coordinateFrame, text="座標：", font=("Helvetica", 10)).pack(
            side="left", padx=(0, 0)
        )

        self.coordinateEntry = tk.Entry(
            coordinateFrame,
            font=("Helvetica", 10),
            state="readonly",
            width=25,
        )
        self.coordinateEntry.pack(padx=(0, 12), side="left", fill="x", expand=True)

        # 右側按鈕
        buttonContainer = tk.Frame(bottomFrame)
        buttonContainer.pack(side="right")

        saveButton = ttk.Button(
            buttonContainer,
            text="儲存選取區域",
            style="primary.Outline.TButton",
            command=self.saveCroppedImage,
        )
        saveButton.pack(padx=(0, 12), side="left")

        getCoordinatesButton = ttk.Button(
            buttonContainer,
            text="取得原圖座標",
            style="primary.Outline.TButton",
            command=self.getOriginalCoordinates,
        )
        getCoordinatesButton.pack(padx=(0, 0), side="left")

    def _updateCoordinateDisplay(self):
        """更新座標顯示"""
        if not self.rectangleCoordinates:
            self.coordinateEntry.config(state="normal")
            self.coordinateEntry.delete(0, tk.END)
            self.coordinateEntry.config(state="readonly")
            return

        x1, y1, x2, y2 = map(int, self.rectangleCoordinates)
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        factor = 1 / self.scale
        originalX1 = int(x1 * factor)
        originalY1 = int(y1 * factor)
        originalX2 = int(x2 * factor)
        originalY2 = int(y2 * factor)

        coordinateText = f"({originalX1}, {originalY1}, {originalX2}, {originalY2})"

        self.coordinateEntry.config(state="normal")
        self.coordinateEntry.delete(0, tk.END)
        self.coordinateEntry.insert(0, coordinateText)
        self.coordinateEntry.config(state="readonly")

    def onMouseDown(self, event):
        """左鍵按下事件，判斷為建立選取或拖曳現有區域"""
        x, y = event.x, event.y
        imageX = x - self.offsetX
        imageY = y - self.offsetY

        if self.rectangleCoordinates:
            handle = self._hitTestHandle(imageX, imageY)

            if handle:
                self.isDragging = True
                self.dragHandle = handle
                return

            if self._pointInRectangle(imageX, imageY):
                self.isDragging = True
                self.dragHandle = "move"
                self.startX = imageX
                self.startY = imageY
                return

        if not self.rectangleCoordinates:
            self.isDragging = True
            self.dragHandle = None
            self.rectangleCoordinates = [imageX, imageY, imageX, imageY]
            self._drawRectangle()

    def onMouseMove(self, event):
        """左鍵移動事件，調整選取區域的大小或位置"""
        if not self.isDragging:
            return

        x, y = event.x, event.y
        imageX = x - self.offsetX
        imageY = y - self.offsetY

        # 限制滑鼠座標不能超出圖片邊界
        imageX = max(0, min(imageX, self.imageWidth))
        imageY = max(0, min(imageY, self.imageHeight))

        # 將目前的滑鼠位置更新為矩形的右下角座標
        if self.dragHandle is None:
            self.rectangleCoordinates[2] = imageX
            self.rectangleCoordinates[3] = imageY

        elif self.dragHandle == "move":
            # 計算移動距離
            deltaX = imageX - self.startX
            deltaY = imageY - self.startY

            # 更新起點，下次移動時使用
            self.startX = imageX
            self.startY = imageY

            # 矩形移動後的座標
            x1, y1, x2, y2 = self.rectangleCoordinates
            x1 += deltaX
            y1 += deltaY
            x2 += deltaX
            y2 += deltaY

            # 若矩形超出圖片範圍，則讓矩形維持同樣的寬高
            if x1 < 0:
                x2 -= x1
                x1 = 0
            if y1 < 0:
                y2 -= y1
                y1 = 0
            if x2 > self.imageWidth:
                x1 -= x2 - self.imageWidth
                x2 = self.imageWidth
            if y2 > self.imageHeight:
                y1 -= y2 - self.imageHeight
                y2 = self.imageHeight

            self.rectangleCoordinates = [x1, y1, x2, y2]

        else:
            x1, y1, x2, y2 = self.rectangleCoordinates

            # 限制拖曳點，不可以讓框選矩形縮到太小或反向
            if self.dragHandle == "left":
                x1 = min(max(0, imageX), x2 - 5)
            elif self.dragHandle == "right":
                x2 = max(min(self.imageWidth, imageX), x1 + 5)
            elif self.dragHandle == "top":
                y1 = min(max(0, imageY), y2 - 5)
            elif self.dragHandle == "bottom":
                y2 = max(min(self.imageHeight, imageY), y1 + 5)

            self.rectangleCoordinates = [x1, y1, x2, y2]

        self._drawRectangle()

    def onMouseUp(self, event):
        """左鍵放開事件，結束拖曳操作"""
        self.isDragging = False
        self.dragHandle = None

    def onDoubleClick(self, event):
        """左鍵雙擊事件，取消選取"""
        x, y = event.x, event.y
        imageX = x - self.offsetX
        imageY = y - self.offsetY

        # 若在選取框和控制點之外雙擊，則清除整個選取框
        if self.rectangleCoordinates:
            if not self._pointInRectangle(imageX, imageY) and not self._hitTestHandle(
                imageX, imageY
            ):
                self.cancelSelection()

    def _drawRectangle(self):
        """繪製選取矩形和控制點"""

        # 清除舊的矩形框與控制點
        if self.rectangleId:
            self.canvas.delete(self.rectangleId)
        for handle in self.handles.values():
            self.canvas.delete(handle)
        self.handles.clear()

        # 清除舊的遮罩
        if hasattr(self, "maskIds"):
            for maskId in self.maskIds:
                self.canvas.delete(maskId)
        self.maskIds = []

        # 若沒有選取座標，更新座標顯示後結束
        if not self.rectangleCoordinates:
            self._updateCoordinateDisplay()
            return

        # 確保左上角與右下角的順序正確
        x1, y1, x2, y2 = self.rectangleCoordinates
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        self.rectangleCoordinates = [x1, y1, x2, y2]

        # 畫紅色的矩形框
        self.rectangleId = self.canvas.create_rectangle(
            x1 + self.offsetX,
            y1 + self.offsetY,
            x2 + self.offsetX,
            y2 + self.offsetY,
            outline="red",
            width=2,
        )

        # 計算遮罩區域，將矩形的座標轉換為在 Canvas 上的位置
        width = self.WINDOW_WIDTH
        height = self.WINDOW_HEIGHT - self.PANEL_HEIGHT
        canvasX1 = x1 + self.offsetX
        canvasY1 = y1 + self.offsetY
        canvasX2 = x2 + self.offsetX
        canvasY2 = y2 + self.offsetY

        # 繪製矩形外的遮罩
        self.maskIds.append(
            self.canvas.create_rectangle(
                0, 0, width, canvasY1, fill="gray20", stipple="gray50", outline=""
            )
        )
        self.maskIds.append(
            self.canvas.create_rectangle(
                0, canvasY2, width, height, fill="gray20", stipple="gray50", outline=""
            )
        )
        self.maskIds.append(
            self.canvas.create_rectangle(
                0,
                canvasY1,
                canvasX1,
                canvasY2,
                fill="gray20",
                stipple="gray50",
                outline="",
            )
        )
        self.maskIds.append(
            self.canvas.create_rectangle(
                canvasX2,
                canvasY1,
                width,
                canvasY2,
                fill="gray20",
                stipple="gray50",
                outline="",
            )
        )

        # 畫四個控制點
        handlePositions = {
            "left": (canvasX1, (canvasY1 + canvasY2) / 2),
            "right": (canvasX2, (canvasY1 + canvasY2) / 2),
            "top": ((canvasX1 + canvasX2) / 2, canvasY1),
            "bottom": ((canvasX1 + canvasX2) / 2, canvasY2),
        }

        for position, (handleX, handleY) in handlePositions.items():
            handle = self.canvas.create_rectangle(
                handleX - self.HANDLE_SIZE // 2,
                handleY - self.HANDLE_SIZE // 2,
                handleX + self.HANDLE_SIZE // 2,
                handleY + self.HANDLE_SIZE // 2,
                fill="white",
                outline="black",
                width=1,
            )
            self.handles[position] = handle

        # 更新座標顯示
        self._updateCoordinateDisplay()

    def _hitTestHandle(self, x, y):
        """檢測是否點擊到控制點"""
        if not self.handles:
            return None

        for name, handleId in self.handles.items():
            coordinates = self.canvas.coords(handleId)

            x1, y1, x2, y2 = coordinates
            x1 -= self.offsetX
            x2 -= self.offsetX
            y1 -= self.offsetY
            y2 -= self.offsetY

            if x1 <= x <= x2 and y1 <= y <= y2:
                return name

        return None

    def _pointInRectangle(self, x, y):
        """檢測點是否在矩形內"""
        if not self.rectangleCoordinates:
            return False

        x1, y1, x2, y2 = self.rectangleCoordinates
        return x1 <= x <= x2 and y1 <= y <= y2

    def cancelSelection(self):
        """取消選取"""
        if self.rectangleId:
            self.canvas.delete(self.rectangleId)
            self.rectangleId = None

        for handle in self.handles.values():
            self.canvas.delete(handle)
        self.handles.clear()

        self.rectangleCoordinates = None

        for maskId in getattr(self, "maskIds", []):
            self.canvas.delete(maskId)

        self._updateCoordinateDisplay()

    def onRightMouseDown(self, event):
        """右鍵按下事件，開始拖曳圖片"""
        self.isDraggingImage = True
        self.dragImageStart = (event.x, event.y)
        self.startOffsetX = self.offsetX
        self.startOffsetY = self.offsetY

    def onRightMouseMove(self, event):
        """右鍵移動事件，拖曳圖片"""
        if not self.isDraggingImage:
            return

        deltaX = event.x - self.dragImageStart[0]
        deltaY = event.y - self.dragImageStart[1]

        newOffsetX = self.startOffsetX + deltaX
        newOffsetY = self.startOffsetY + deltaY

        maxOffsetX = 0
        maxOffsetY = 0
        minOffsetX = min(0, self.canvas.winfo_width() - self.imageWidth)
        minOffsetY = min(0, self.canvas.winfo_height() - self.imageHeight)

        self.offsetX = max(minOffsetX, min(maxOffsetX, newOffsetX))
        self.offsetY = max(minOffsetY, min(maxOffsetY, newOffsetY))

        self.canvas.coords(self.imageId, self.offsetX, self.offsetY)
        self._drawRectangle()

    def onRightMouseUp(self, event):
        """右鍵放開事件，結束拖曳"""
        self.isDraggingImage = False

    def onMouseWheel(self, event):
        """滑鼠滾輪事件，縮放圖片"""
        oldScale = self.scale

        # 根據滾動方向，決定新的縮放值
        tentativeScale = (
            self.scale + self.SCALE_STEP
            if (event.delta > 0)
            else self.scale - self.SCALE_STEP
        )

        # 計算圖片是否比視窗大
        isImageWider = self.originalImage.width > self.WINDOW_WIDTH
        isImageTaller = self.originalImage.height > (
            self.WINDOW_HEIGHT - self.PANEL_HEIGHT
        )

        # 若圖片比視窗大，最小縮放到兩邊都能完整顯示
        if isImageWider or isImageTaller:
            minScaleX = self.WINDOW_WIDTH / self.originalImage.width
            minScaleY = (
                self.WINDOW_HEIGHT - self.PANEL_HEIGHT
            ) / self.originalImage.height
            minAllowedScale = min(minScaleX, minScaleY)

        # 若圖片比視窗小，最小縮放限制為 1.0 (原始大小)
        else:
            minAllowedScale = 1.0

        newScale = min(self.MAX_SCALE, max(minAllowedScale, tentativeScale))

        if newScale == self.scale:
            return

        canvasMouseX = self.canvas.canvasx(event.x)
        canvasMouseY = self.canvas.canvasy(event.y)
        imageMouseX = canvasMouseX - self.offsetX
        imageMouseY = canvasMouseY - self.offsetY

        # 若滑鼠不在圖片內，則不進行縮放
        if not (
            0 <= imageMouseX <= self.imageWidth and 0 <= imageMouseY <= self.imageHeight
        ):
            return

        # 更新縮放比例與圖片大小
        scaleRatio = newScale / oldScale
        self.scale = newScale

        width, height = self.originalImage.size
        self.imageWidth = int(width * self.scale)
        self.imageHeight = int(height * self.scale)
        self.image = self.originalImage.resize(
            (self.imageWidth, self.imageHeight), Image.LANCZOS
        )
        self.photo = ImageTk.PhotoImage(self.image)
        self.canvas.itemconfig(self.imageId, image=self.photo)

        # 更新 offset，縮放中心以鼠標為基準
        self.offsetX = int(canvasMouseX - imageMouseX * scaleRatio)
        self.offsetY = int(canvasMouseY - imageMouseY * scaleRatio)

        # 限制圖片在畫布中可移動的範圍
        maxOffsetX = 0
        maxOffsetY = 0
        minOffsetX = min(0, self.canvas.winfo_width() - self.imageWidth)
        minOffsetY = min(0, self.canvas.winfo_height() - self.imageHeight)

        self.offsetX = max(minOffsetX, min(maxOffsetX, self.offsetX))
        self.offsetY = max(minOffsetY, min(maxOffsetY, self.offsetY))

        self.canvas.coords(self.imageId, self.offsetX, self.offsetY)

        # 更新框選區座標與重新繪製
        if self.rectangleCoordinates:
            self.rectangleCoordinates = [
                coordinate * scaleRatio for coordinate in self.rectangleCoordinates
            ]
        self._drawRectangle()

    def saveCroppedImage(self):
        """儲存裁切後的圖片"""
        if not self.rectangleCoordinates:
            messagebox.showwarning("警告", "尚未選取區域", parent=self)
            return

        x1, y1, x2, y2 = map(int, self.rectangleCoordinates)
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        factor = 1 / self.scale
        originalCoordinates = (
            int(x1 * factor),
            int(y1 * factor),
            int(x2 * factor),
            int(y2 * factor),
        )

        croppedImage = self.originalImage.crop(originalCoordinates)
        savePath = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("所有檔案", "*.*")],
        )

        if savePath:
            croppedImage.save(savePath)
            messagebox.showinfo("完成", f"圖片已儲存至\n{savePath}", parent=self)

    def getOriginalCoordinates(self):
        """取得原圖座標並複製到剪貼簿"""
        if not self.rectangleCoordinates:
            messagebox.showinfo("提示", "尚未選取區域", parent=self)
            return

        x1, y1, x2, y2 = map(int, self.rectangleCoordinates)
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])
        factor = 1 / self.scale
        originalX1 = int(x1 * factor)
        originalY1 = int(y1 * factor)
        originalX2 = int(x2 * factor)
        originalY2 = int(y2 * factor)

        coordinateText = f"({originalX1}, {originalY1}, {originalX2}, {originalY2})"

        self.clipboard_clear()
        self.clipboard_append(coordinateText)
        self.update()

        messagebox.showinfo(
            "完成", f"座標已複製到剪貼簿\n{coordinateText}", parent=self
        )


def openImageCropper(root):
    """開啟圖片裁切器"""
    imagePath = filedialog.askopenfilename(
        parent=root,
        title="選擇圖片",
        filetypes=[("圖片檔案", "*.png *.jpg *.jpeg *.bmp")],
    )

    if not imagePath:
        messagebox.showwarning("警告", "未選擇圖片", parent=root)
        return

    ImageCropper(root, imagePath)


if __name__ == "__main__":
    root = tk.Tk()

    # 隱藏主視窗
    root.withdraw()

    openImageCropper(root)
    root.mainloop()
