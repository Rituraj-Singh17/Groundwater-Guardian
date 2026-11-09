from sqlalchemy import (
    Column, String, Integer, BigInteger, Numeric, DateTime,
    ForeignKey, Text, Boolean, JSON, UniqueConstraint, Index,
    func
)
from sqlalchemy.orm import relationship

from app.database import Base


class Station(Base):
    __tablename__ = "stations"

    station_id = Column(String(32), primary_key=True)
    station_name = Column(String(200), nullable=False, index=True)
    agency = Column(String(100))
    state_lgd_code = Column(Integer)
    state = Column(String(100))
    district_lgd_code = Column(Integer)
    district = Column(String(100), index=True)
    latitude = Column(Numeric(10, 6))
    longitude = Column(Numeric(10, 6))
    rl_msl = Column(Numeric(12, 3))

    observations = relationship("Observation", back_populates="station")
    alerts = relationship("Alert", back_populates="station")
    reliability = relationship(
        "StationReliability",
        back_populates="station",
        uselist=False
    )


class Observation(Base):
    __tablename__ = "observations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    station_id = Column(
        String(32),
        ForeignKey("stations.station_id", ondelete="RESTRICT"),
        nullable=False
    )
    source_slno = Column(BigInteger)
    observed_at = Column(DateTime(timezone=False), nullable=False)
    groundwater_level_m = Column(Numeric(12, 3), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    station = relationship("Station", back_populates="observations")
    alerts = relationship("Alert", back_populates="observation")

    __table_args__ = (
        UniqueConstraint(
            "station_id", "observed_at",
            name="uq_observation_station_time"
        ),
        Index("ix_observations_station_time", "station_id", "observed_at"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    station_id = Column(
        String(32),
        ForeignKey("stations.station_id", ondelete="RESTRICT"),
        nullable=False
    )
    observation_id = Column(
        BigInteger,
        ForeignKey("observations.id", ondelete="SET NULL")
    )
    alert_type = Column(String(60), nullable=False)
    severity = Column(String(20), nullable=False)
    explanation = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="open")
    detected_at = Column(DateTime, server_default=func.now())
    resolved_at = Column(DateTime)
    start_at = Column(DateTime)
    end_at = Column(DateTime)
    evidence = Column(JSON)

    station = relationship("Station", back_populates="alerts")
    observation = relationship("Observation", back_populates="alerts")
    maintenance_records = relationship(
        "MaintenanceRecord", back_populates="alert"
    )

    __table_args__ = (
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_station", "station_id"),
        Index(
            "uq_alert_identity",
            "station_id",
            "alert_type",
            "detected_at",
            unique=True
        ),
    )


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    alert_id = Column(
        BigInteger,
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False
    )
    assigned_to = Column(String(150))
    status = Column(String(30), nullable=False, default="open")
    notes = Column(Text)
    opened_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime)

    alert = relationship("Alert", back_populates="maintenance_records")


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    random_seed = Column(Integer)
    status = Column(String(30), nullable=False, default="created")
    configuration = Column(JSON)
    evaluation_results = Column(JSON)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    injected_faults = relationship(
        "InjectedFault", back_populates="simulation_run"
    )


class InjectedFault(Base):
    __tablename__ = "injected_faults"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    simulation_run_id = Column(
        BigInteger,
        ForeignKey("simulation_runs.id", ondelete="CASCADE"),
        nullable=False
    )
    station_id = Column(
        String(32),
        ForeignKey("stations.station_id", ondelete="RESTRICT"),
        nullable=False
    )
    fault_type = Column(String(60), nullable=False)
    start_at = Column(DateTime)
    end_at = Column(DateTime)
    parameters = Column(JSON)
    ground_truth = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now())

    simulation_run = relationship(
        "SimulationRun", back_populates="injected_faults"
    )
    station = relationship("Station")

class StationReliability(Base):
    __tablename__ = "station_reliability"

    station_id = Column(
        String(32),
        ForeignKey("stations.station_id", ondelete="CASCADE"),
        primary_key=True
    )

    total_observations = Column(Integer, nullable=False)
    expected_observations = Column(Integer, nullable=False)
    valid_observations = Column(Integer, nullable=False)

    estimated_missing_observations = Column(Numeric(12, 2))
    missing_alerts = Column(Integer, nullable=False)
    flatline_repeated_alerts = Column(Integer, nullable=False)
    sudden_change_alerts = Column(Integer, nullable=False)

    missing_rate_per_1000 = Column(Numeric(12, 2))
    flatline_rate_per_1000 = Column(Numeric(12, 2))
    sudden_rate_per_1000 = Column(Numeric(12, 2))

    missing_quality = Column(Numeric(6, 2))
    flatline_quality = Column(Numeric(6, 2))
    sudden_quality = Column(Numeric(6, 2))
    completeness = Column(Numeric(6, 2))

    missing_quality_contribution = Column(Numeric(6, 2))
    flatline_quality_contribution = Column(Numeric(6, 2))
    sudden_quality_contribution = Column(Numeric(6, 2))
    completeness_contribution = Column(Numeric(6, 2))

    reliability_score = Column(Numeric(6, 2), nullable=False, index=True)
    reliability_category = Column(String(30), nullable=False, index=True)

    primary_concern = Column(String(100))
    explanation = Column(Text)
    recommended_action = Column(Text)
    investigation_priority = Column(String(30), index=True)

    calculated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    station = relationship("Station")
