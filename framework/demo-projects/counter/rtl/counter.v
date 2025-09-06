module counter(
    input wire clk,          // 时钟输入
    input wire rst_n,        // 低电平有效的复位信号
    output reg [3:0] count   // 4位计数器输出
);

    // 计数器逻辑
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 4'b0000;  // 复位时清零
        end else begin
            count <= count + 1'b1;  // 每个时钟周期加1
        end
    end

endmodule 