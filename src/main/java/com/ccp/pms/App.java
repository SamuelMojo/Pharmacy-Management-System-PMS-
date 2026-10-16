package com.ccp.pms;

import javafx.application.Application;
import javafx.scene.Scene;
import javafx.scene.control.Label;
import javafx.stage.Stage;

public class App extends Application {
    @Override
    public void start(Stage stage) {
        stage.setScene(new Scene(new Label("PMS is running"), 400, 200));
        stage.setTitle("Pharmacy Management System");
        stage.show();
    }

    public static void main(String[] args) {
        launch(args);
    }
}