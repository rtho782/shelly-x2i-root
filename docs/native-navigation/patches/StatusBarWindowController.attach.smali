# Modified 2026: smali adaptation of the cited AOSP methods for the exact documented Shelly APK.
# Not a complete class except RestoredNavigationAttach; see ../README.md.
# Adapted from AOSP StatusBarWindowController.attach, android11-release.
# Copyright (C) 2019 The Android Open Source Project, Apache-2.0.
# https://www.apache.org/licenses/LICENSE-2.0
.method public attach()V
    .locals 7
    new-instance v0, Landroid/view/WindowManager$LayoutParams;
    const/4 v1, -0x1
    iget v2, p0, Lcom/android/systemui/statusbar/phone/StatusBarWindowController;->mBarHeight:I
    const/16 v3, 0x7d0
    const v4, -0x7f7ffff8
    const/4 v5, -0x3
    invoke-direct/range {v0 .. v5}, Landroid/view/WindowManager$LayoutParams;-><init>(IIIII)V
    iput-object v0, p0, Lcom/android/systemui/statusbar/phone/StatusBarWindowController;->mLp:Landroid/view/WindowManager$LayoutParams;
    move-object v6, v0
    sget v0, Landroid/view/WindowManager$LayoutParams;->PRIVATE_FLAG_COLOR_SPACE_AGNOSTIC:I
    iput v0, v6, Landroid/view/WindowManager$LayoutParams;->privateFlags:I
    new-instance v0, Landroid/os/Binder;
    invoke-direct {v0}, Landroid/os/Binder;-><init>()V
    iput-object v0, v6, Landroid/view/WindowManager$LayoutParams;->token:Landroid/os/IBinder;
    const/16 v0, 0x30
    iput v0, v6, Landroid/view/WindowManager$LayoutParams;->gravity:I
    const/4 v0, 0x0
    invoke-virtual {v6, v0}, Landroid/view/WindowManager$LayoutParams;->setFitInsetsTypes(I)V
    const-string v0, "StatusBar"
    invoke-virtual {v6, v0}, Landroid/view/WindowManager$LayoutParams;->setTitle(Ljava/lang/CharSequence;)V
    const-string v0, "com.android.systemui"
    iput-object v0, v6, Landroid/view/WindowManager$LayoutParams;->packageName:Ljava/lang/String;
    const/4 v0, 0x3
    iput v0, v6, Landroid/view/WindowManager$LayoutParams;->layoutInDisplayCutoutMode:I
    iget-object v0, p0, Lcom/android/systemui/statusbar/phone/StatusBarWindowController;->mWindowManager:Landroid/view/WindowManager;
    iget-object v1, p0, Lcom/android/systemui/statusbar/phone/StatusBarWindowController;->mStatusBarView:Landroid/view/ViewGroup;
    invoke-interface {v0, v1, v6}, Landroid/view/WindowManager;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V
    iget-object v0, p0, Lcom/android/systemui/statusbar/phone/StatusBarWindowController;->mLpChanged:Landroid/view/WindowManager$LayoutParams;
    invoke-virtual {v0, v6}, Landroid/view/WindowManager$LayoutParams;->copyFrom(Landroid/view/WindowManager$LayoutParams;)I
    return-void
.end method
