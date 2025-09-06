`timescale 1ns/1ps

module counter_tb;
    // 定义信号
    reg clk;
    reg rst_n;
    wire [3:0] count;

    // 实例化被测模块
    counter uut (
        .clk(clk),
        .rst_n(rst_n),
        .count(count)
    );

    // 时钟生成
    initial begin
        #0; // 增加一个零延时
        clk = 0;
        forever #5 clk = ~clk;  // 10ns周期
    end

    // 测试激励
    initial begin
        // 初始化波形文件
        $dumpfile("waveform.vcd");
        $dumpvars(0, counter_tb);

        // 初始状态
        rst_n = 0;
        #20;  // 等待2个时钟周期

        // 释放复位
        rst_n = 1;
        #200;  // 运行20个时钟周期

        // 再次复位
        rst_n = 0;
        #20;

        // 再次释放复位
        rst_n = 1;
        #100;

        // 结束仿真
        $finish;
    end

    // 监控输出
    initial begin
        $monitor("Time=%0t rst_n=%b count=%b", $time, rst_n, count);
    end

endmodule 