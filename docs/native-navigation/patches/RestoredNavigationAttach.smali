# Modified 2026: smali adaptation of the cited AOSP methods for the exact documented Shelly APK.
# Not a complete class except RestoredNavigationAttach; see ../README.md.
# Adapted from AOSP NavigationBarFragment.create's attach listener, Android 11.
# Copyright (C) 2017 The Android Open Source Project, Apache-2.0.
# https://www.apache.org/licenses/LICENSE-2.0
.class final Lcom/android/systemui/statusbar/phone/RestoredNavigationAttach;
.super Ljava/lang/Object;
.implements Landroid/view/View$OnAttachStateChangeListener;

.field private final fragment:Lcom/android/systemui/statusbar/phone/NavigationBarFragment;
.field private final listener:Lcom/android/systemui/fragments/FragmentHostManager$FragmentListener;

.method public constructor <init>(Lcom/android/systemui/statusbar/phone/NavigationBarFragment;Lcom/android/systemui/fragments/FragmentHostManager$FragmentListener;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/android/systemui/statusbar/phone/RestoredNavigationAttach;->fragment:Lcom/android/systemui/statusbar/phone/NavigationBarFragment;
    iput-object p2, p0, Lcom/android/systemui/statusbar/phone/RestoredNavigationAttach;->listener:Lcom/android/systemui/fragments/FragmentHostManager$FragmentListener;
    return-void
.end method

.method public onViewAttachedToWindow(Landroid/view/View;)V
    .locals 5
    invoke-static {p1}, Lcom/android/systemui/fragments/FragmentHostManager;->get(Landroid/view/View;)Lcom/android/systemui/fragments/FragmentHostManager;
    move-result-object v0
    invoke-virtual {v0}, Lcom/android/systemui/fragments/FragmentHostManager;->getFragmentManager()Landroid/app/FragmentManager;
    move-result-object v1
    invoke-virtual {v1}, Landroid/app/FragmentManager;->beginTransaction()Landroid/app/FragmentTransaction;
    move-result-object v1
    const v2, 0x7f0a0327
    iget-object v3, p0, Lcom/android/systemui/statusbar/phone/RestoredNavigationAttach;->fragment:Lcom/android/systemui/statusbar/phone/NavigationBarFragment;
    const-string v4, "NavigationBar"
    invoke-virtual {v1, v2, v3, v4}, Landroid/app/FragmentTransaction;->replace(ILandroid/app/Fragment;Ljava/lang/String;)Landroid/app/FragmentTransaction;
    move-result-object v1
    invoke-virtual {v1}, Landroid/app/FragmentTransaction;->commit()I
    iget-object v1, p0, Lcom/android/systemui/statusbar/phone/RestoredNavigationAttach;->listener:Lcom/android/systemui/fragments/FragmentHostManager$FragmentListener;
    invoke-virtual {v0, v4, v1}, Lcom/android/systemui/fragments/FragmentHostManager;->addTagListener(Ljava/lang/String;Lcom/android/systemui/fragments/FragmentHostManager$FragmentListener;)Lcom/android/systemui/fragments/FragmentHostManager;
    return-void
.end method

.method public onViewDetachedFromWindow(Landroid/view/View;)V
    .locals 0
    invoke-static {p1}, Lcom/android/systemui/fragments/FragmentHostManager;->removeAndDestroy(Landroid/view/View;)V
    invoke-virtual {p1, p0}, Landroid/view/View;->removeOnAttachStateChangeListener(Landroid/view/View$OnAttachStateChangeListener;)V
    return-void
.end method
