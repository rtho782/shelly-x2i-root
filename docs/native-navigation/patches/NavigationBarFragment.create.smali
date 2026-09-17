# Modified 2026: smali adaptation of the cited AOSP methods for the exact documented Shelly APK.
# Not a complete class except RestoredNavigationAttach; see ../README.md.
# Adapted from AOSP NavigationBarFragment.create, Android 11.
# Copyright (C) 2017 The Android Open Source Project, Apache-2.0.
# https://www.apache.org/licenses/LICENSE-2.0
.method public static create(Landroid/content/Context;Lcom/android/systemui/fragments/FragmentHostManager$FragmentListener;)Landroid/view/View;
    .locals 7

    new-instance v0, Landroid/view/WindowManager$LayoutParams;
    const/4 v1, -0x1
    const/4 v2, -0x1
    const/16 v3, 0x7e3
    const v4, 0x20840068
    const/4 v5, -0x3
    invoke-direct/range {v0 .. v5}, Landroid/view/WindowManager$LayoutParams;-><init>(IIIII)V
    move-object v6, v0

    new-instance v0, Landroid/os/Binder;
    invoke-direct {v0}, Landroid/os/Binder;-><init>()V
    iput-object v0, v6, Landroid/view/WindowManager$LayoutParams;->token:Landroid/os/IBinder;
    const-string v0, "NavigationBar0"
    invoke-virtual {v6, v0}, Landroid/view/WindowManager$LayoutParams;->setTitle(Ljava/lang/CharSequence;)V
    const v0, 0x7f11046b
    invoke-virtual {p0, v0}, Landroid/content/Context;->getString(I)Ljava/lang/String;
    move-result-object v0
    iput-object v0, v6, Landroid/view/WindowManager$LayoutParams;->accessibilityTitle:Ljava/lang/CharSequence;
    const/4 v0, 0x0
    iput v0, v6, Landroid/view/WindowManager$LayoutParams;->windowAnimations:I
    sget v0, Landroid/view/WindowManager$LayoutParams;->PRIVATE_FLAG_COLOR_SPACE_AGNOSTIC:I
    iget v1, v6, Landroid/view/WindowManager$LayoutParams;->privateFlags:I
    or-int/2addr v0, v1
    iput v0, v6, Landroid/view/WindowManager$LayoutParams;->privateFlags:I

    invoke-static {p0}, Landroid/view/LayoutInflater;->from(Landroid/content/Context;)Landroid/view/LayoutInflater;
    move-result-object v0
    const v1, 0x7f0d0105
    const/4 v2, 0x0
    invoke-virtual {v0, v1, v2}, Landroid/view/LayoutInflater;->inflate(ILandroid/view/ViewGroup;)Landroid/view/View;
    move-result-object v0

    invoke-static {v0}, Lcom/android/systemui/fragments/FragmentHostManager;->get(Landroid/view/View;)Lcom/android/systemui/fragments/FragmentHostManager;
    move-result-object v1
    const-class v2, Lcom/android/systemui/statusbar/phone/NavigationBarFragment;
    invoke-virtual {v1, v2}, Lcom/android/systemui/fragments/FragmentHostManager;->create(Ljava/lang/Class;)Ljava/lang/Object;
    move-result-object v1
    check-cast v1, Lcom/android/systemui/statusbar/phone/NavigationBarFragment;
    new-instance v2, Lcom/android/systemui/statusbar/phone/RestoredNavigationAttach;
    invoke-direct {v2, v1, p1}, Lcom/android/systemui/statusbar/phone/RestoredNavigationAttach;-><init>(Lcom/android/systemui/statusbar/phone/NavigationBarFragment;Lcom/android/systemui/fragments/FragmentHostManager$FragmentListener;)V
    invoke-virtual {v0, v2}, Landroid/view/View;->addOnAttachStateChangeListener(Landroid/view/View$OnAttachStateChangeListener;)V

    const-class v1, Landroid/view/WindowManager;
    invoke-virtual {p0, v1}, Landroid/content/Context;->getSystemService(Ljava/lang/Class;)Ljava/lang/Object;
    move-result-object v1
    check-cast v1, Landroid/view/WindowManager;
    invoke-interface {v1, v0, v6}, Landroid/view/WindowManager;->addView(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V
    return-object v0
.end method
