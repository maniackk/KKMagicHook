//
//  ViewController.m
//  KKMagicHook
//
//  Created by 吴凯凯 on 2020/3/20.
//  Copyright © 2020 吴凯凯. All rights reserved.
//

#import "ViewController.h"
#import "lib/staticLib_arm64.h"

@interface ViewController ()

@end

@implementation ViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    // Do any additional setup after loading the view.
    staticLib_arm64 *obj = [staticLib_arm64 new];
    [obj method1];
    [obj method2];
}


@end
